from __future__ import annotations
from typing import Type, TypeVar, List, Tuple, Generator, Optional, Literal
from datetime import datetime
from pathlib import Path

import pandas as pd
import igraph as ig
from igraph.drawing.cairo.plot import CairoPlot
from pydantic import BaseModel
from wordcloud import WordCloud

from scraping_kit.db.db_twitter import DBTwitter
from scraping_kit.db.models.user_full import UsersFullData
from scraping_kit.utils import format_date_yyyy_mm_dd
from scraping_kit.keywords import (
    T_Keywords, KeyCol, get_blacklist_words, tweets2keywords, keywords_update
)


class GraphPlotStyle(BaseModel):
    bbox: Tuple[int, int] = (800, 800)
    margin: int = 70
    vertex_size: int = 10
    vertex_label_dist: int = 2
    vertex_label_color: str = "#bd93f9"
    vertex_color: str = "#2E6E8E"
    background: str = "#282a36"
    edge_color: str = "#6272a4"
    edge_arrow_size: int = 1
    edge_arrow_width: int = 1
    edge_curved: bool = True
    layout: str = "auto"











class KeywordsCluster:
    def __init__(self, keywords: T_Keywords, profiles: list, idx: int = None):
        self.keywords = keywords
        self.profiles = profiles
        self.idx = idx
    
    @property
    def _col(self) -> str:
        if self.idx is None:
            return ""
        return f"cluster {self.idx}: "

    @property
    def kw_col(self) -> str:
        return self._col + "kw"
    
    @property
    def count_col(self) -> str:
        return self._col + "count"

    @property
    def profiles_col(self) -> str:
        return self._col + "profiles"

    @property
    def n_users(self) -> int:
        return len(self.profiles)

    def __str__(self) -> str:
        return f"Cluster(idx={self.idx} | n_users={self.n_users} | users={self.profiles})"
    
    def __repr__(self) -> str:
        return self.__str__()

    def iter_kw_count(self) -> Generator[Tuple[str, int], None, None]:
        return ((kw, c) for kw, c in self.keywords.items())

    def kw_count_sort_list(self) -> Tuple[Tuple[str], Tuple[int]]:
        if len(self.keywords) != 0:
            l = list(self.keywords.items())
            l.sort(key=lambda item: item[1], reverse=True)
            kw, count = zip(*l)
        else:
            kw, count = [], []
        return {self.kw_col: kw, self.count_col: count}

    def df_cluster(self) -> pd.DataFrame:
        df = pd.DataFrame(self.kw_count_sort_list())
        profiles = self.profiles.copy()
        profiles += [""] * (len(self.keywords) - self.n_users)
        df.insert(0, self.profiles_col, profiles)
        return df

    @classmethod
    def from_subgraph(cls, idx: int, subgraph: ig.Graph) -> KeywordsCluster:
        keywords = {}
        for kw in subgraph.vs[KeyCol.KEYWORDS]:
            keywords_update(keywords, kw)
        
        profiles = [(v[KeyCol.NAME], v[KeyCol.FOLLOWERS]) for v in subgraph.vs]
        profiles = [v[0] for v in sorted(profiles, key=lambda item: item[1], reverse=True)]
        
        return KeywordsCluster(
            keywords = keywords,
            profiles = profiles,
            idx = idx
        )


class KWClusters(List[KeywordsCluster]):
    def __init__(self, path_folder_keywords: Path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path_folder_keywords = path_folder_keywords
    
    @property
    def path_folder_keywords_cluster(self) -> Path:
        path_folder_keywords = self.path_folder_keywords / "clusters"
        path_folder_keywords.mkdir(exist_ok=True)
        return path_folder_keywords

    @classmethod
    def from_graph_follow(cls, graph_follow: GraphFollows, min_users_per_cluster=2) -> KWClusters:
        assert min_users_per_cluster >= 2, "The minimum number users per clusters must be 2."
        kw_clusters = KWClusters(graph_follow.path_folder_keywords)
        for idx, subgraph in graph_follow.iter_subgraph(min_users_per_cluster):
            kw_cluster = KeywordsCluster.from_subgraph(idx, subgraph)
            kw_clusters.append(kw_cluster)
        kw_clusters.sort(key=lambda cluster: cluster.n_users, reverse=True)
        return kw_clusters

    def save_keywords_clusters(self):
        for kw_cluster in self:
            path_cluster = self.path_folder_keywords_cluster / f"cluster_{kw_cluster.idx}.csv"
            df_cluster = kw_cluster.df_cluster()
            df_cluster.to_csv(path_cluster)

    def __str__(self) -> str:
        return "\n".join((cluster.__str__() for cluster in self))
    
    def __repr__(self) -> str:
        return self.__str__()







T_GraphFollows = TypeVar("T_GraphFollows", bound="GraphFollows")

class GraphFollows:
    def __init__(
            self,
            graph: ig.Graph,
            default_plot_style: GraphPlotStyle,
            path_folder_out: Path,
            wc: WordCloud,
            date_i: datetime,
            date_f: datetime
        ):
        self.graph: ig.Graph = graph
        self._g: Optional[ig.Graph] = None      # Aquí se guardará como caché la copia del grafo pero no dirigido.
        self.default_plot_style = default_plot_style
        self.path_folder_out: Path = path_folder_out
        self.wc: WordCloud = wc
        self.date_i: datetime = date_i
        self.date_f: datetime = date_f
    
    @property
    def format_folder(self) -> str:
        date_str_from = format_date_yyyy_mm_dd(self.date_i)
        date_str_to = format_date_yyyy_mm_dd(self.date_f)
        return f"from_{date_str_from}_to_{date_str_to}"
    
    @property
    def path_folder_range(self) -> Path:
        return self.path_folder_out / self.format_folder
    
    @property
    def path_folder_keywords(self) -> Path:
        path_folder_keywords = self.path_folder_range / "keywords"
        path_folder_keywords.mkdir(exist_ok=True)
        return path_folder_keywords

    @property
    def path_folder_keywords_users(self) -> Path:
        path_folder_keywords_users = self.path_folder_keywords / "users"
        path_folder_keywords_users.mkdir(exist_ok=True)
        return path_folder_keywords_users

    @property
    def profiles(self) -> List[str]:
        return self.graph.vs[KeyCol.NAME]
    
    @property
    def g(self) -> ig.Graph:
        """ Almacena como caché el grafo no direccionado para obtener subgraphs."""
        if self._g is None:
            self._g = self.graph.copy()
            self._g.to_undirected()
        return self._g

    def save_keywords_users(self) -> None:
        for v in self.graph.vs:
            name = v[KeyCol.NAME]
            keywords = v[KeyCol.KEYWORDS]
            if len(keywords) > 0:
                df_kw_user = KeywordsCluster(keywords, [name], None).df_cluster()
                df_kw_user.to_csv(self.path_folder_keywords_users / f"{name}.csv")

    def find_name(self, name: str):
        return self.graph.vs.find(name=name)

    def clear_cache(self) -> None:
        self._g = None
    
    def iter_subgraph(self, min_vs=1) -> Generator[Tuple[int, ig.Graph], None, None]:
        idx = 0
        for subgraph in self.g.decompose():
            if len(subgraph.vs) >= min_vs:
                yield idx, subgraph
                idx += 1
        self.clear_cache()

    @classmethod
    def get_attributes(cls, users_full_data: UsersFullData, wc: WordCloud) -> dict[str, list]:
        attributes = {k: [] for k in [KeyCol.NAME, KeyCol.KEYWORDS,
                                      KeyCol.FOLLOWERS, KeyCol.FOLLOWING]}
        
        for user_full in users_full_data.all_users:
            attributes[KeyCol.NAME].append(user_full.profile)
            attributes[KeyCol.KEYWORDS].append(tweets2keywords(wc, user_full.tweets_user))
            attributes[KeyCol.FOLLOWERS].append(user_full.followers)
            attributes[KeyCol.FOLLOWING].append(user_full.following)
        return attributes

    @classmethod
    def from_users_db(
            cls: Type[T_GraphFollows],
            db_tw: DBTwitter,
            users_full_data: UsersFullData,
            date_i: datetime,
            date_f: datetime,
            default_plot_style: GraphPlotStyle = None
        ) -> T_GraphFollows:
        follow_list = db_tw.get_follow_list(users_full_data)
        wc = WordCloud(stopwords=get_blacklist_words(db_tw.path_blacklist_words))
        
        graph = ig.Graph(directed=True)
        graph.add_vertices(
            n = len(users_full_data),
            attributes = cls.get_attributes(users_full_data, wc)
        )
        graph.add_edges(follow_list.list_of_tuples)
        graph.vs[KeyCol.ARROWS_IN] = graph.indegree()
        graph.vs[KeyCol.ARROWS_OUT] = graph.outdegree()

        if default_plot_style is None:
            default_plot_style = GraphPlotStyle()
        
        return cls(
            graph = graph,
            default_plot_style = default_plot_style,
            path_folder_out = db_tw.path_graph_follow_folder,
            wc = wc,
            date_i = date_i,
            date_f = date_f
        )

    def choice_plot_name(self) -> Path:
        i, flag = 0, True
        while flag:
            p = self.path_folder_range / f"graph_follows_{i}.png"
            if not p.exists():
                flag = False
            i += 1
        return p

    def path_out(self) -> Path:
        self.path_folder_range.mkdir(exist_ok=True)
        return self.choice_plot_name()

    def choice_color(self, arrows_in: int, colors_ranges: List[Tuple[int, str]]) -> str:
        for i in range(len(colors_ranges) - 1):
            j = i+1
            if colors_ranges[i][0] <= arrows_in < colors_ranges[j][0]:
                return colors_ranges[i][1]
        return colors_ranges[-1][1]

    def plot(
            self,
            with_save: bool = False,
            plot_style: GraphPlotStyle = None,
            colors_ranges: List[Tuple[int, str]] = None,
            mode: Literal["in", "out", "sum"] = "in"
        ) -> CairoPlot:
        if plot_style is None:
            plot_style = self.default_plot_style.model_dump()
        else:
            plot_style = plot_style.model_dump()
        
        plot_style["vertex_label"] = self.graph.vs[KeyCol.NAME]
        plot_style["layout"] = self.graph.layout("fr")
        if colors_ranges is not None:
            colors_ranges.sort(key=lambda n_c: n_c[0], reverse=False)
            vertex_color = []
            for v in self.graph.vs:
                if mode == "in":
                    criteria = v[KeyCol.ARROWS_IN]
                elif mode == "out":
                    criteria = v[KeyCol.ARROWS_OUT]
                elif mode == "sum":
                    criteria = v[KeyCol.ARROWS_IN] + v[KeyCol.ARROWS_OUT]
                else:
                    raise Exception("Inválid mode: use -> 'in', 'out' or 'sum'.")
                
                color_choiced = self.choice_color(criteria, colors_ranges)
                vertex_color.append(color_choiced)
            plot_style["vertex_color"] = vertex_color

        cairo_plot: CairoPlot = ig.plot(self.graph, **plot_style)
        
        if with_save:
            path_out = self.path_out()
            cairo_plot.save(path_out)

        return cairo_plot
