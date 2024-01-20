from __future__ import annotations
from typing import Type, TypeVar, List, Tuple
from datetime import datetime
from pathlib import Path

import igraph as ig
from igraph.layout import Layout
from igraph.drawing.cairo.plot import CairoPlot
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pydantic import BaseModel

from scraping_kit.db.db_twitter import DBTwitter
from scraping_kit.db.models.users import UserList
from scraping_kit.utils import format_date_full, format_date_yyyy_mm_dd

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


T_GraphFollows = TypeVar("T_GraphFollows", bound="GraphFollows")

class GraphFollows:
    def __init__(
            self,
            graph: ig.Graph,
            default_plot_style: GraphPlotStyle,
            path_folder_out: Path):
        self.graph = graph
        self.default_plot_style = default_plot_style
        self.path_folder_out = path_folder_out
    
    def path_out(self) -> Path:
        date_now = datetime.now()
        path_folder_day = self.path_folder_out / format_date_yyyy_mm_dd(date_now)
        path_folder_day.mkdir(exist_ok=True)
        date_full_str = format_date_full(date_now)
        return path_folder_day / f"graph_follows_{date_full_str}.png"

    @property
    def profiles(self) -> List[str]:
        return self.graph.vs["name"]

    @classmethod
    def from_users_db(
            cls: Type[T_GraphFollows],
            db_tw: DBTwitter,
            users: UserList,
            default_plot_style: GraphPlotStyle = None
        ) -> T_GraphFollows:
        follow_list = db_tw.get_follow_list(users)
        
        graph = ig.Graph(directed=True)
        graph.add_vertices(
            n = len(users),
            attributes = {"name": [user.profile for user in users]}
        )
        graph.add_edges(follow_list.list_of_tuples)
        if default_plot_style is None: default_plot_style=GraphPlotStyle()
        return cls(
            graph = graph,
            default_plot_style = default_plot_style,
            path_folder_out = db_tw.path_graph_follow_folder
        )

    def plot(self, plot_style: GraphPlotStyle = None) -> CairoPlot:
        if plot_style is None:
            plot_style = self.default_plot_style.model_dump()
        else:
            plot_style = plot_style.model_dump()
        
        plot_style["vertex_label"] = self.graph.vs["name"]
        plot_style["layout"] = self.graph.layout("fr")
        cairo_plot: CairoPlot = ig.plot(self.graph, **plot_style)
        
        path_out = self.path_out()
        cairo_plot.save(path_out)

        return cairo_plot
