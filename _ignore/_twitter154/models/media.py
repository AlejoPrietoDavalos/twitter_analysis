from typing import List, Literal

from pydantic import BaseModel

class XYHW(BaseModel):
    x: int
    y: int
    h: int
    w: int

class FacesMedia(BaseModel):
    faces: List[XYHW]

class OriginalInfoMedia(BaseModel):
    height: int
    width: int
    focus_rects: List[XYHW]

class HWResizeMedia(BaseModel):
    h: int
    w: int
    resize: Literal["fit", "crop"]

class SizesMedia(BaseModel):
    large: HWResizeMedia
    medium: HWResizeMedia
    small: HWResizeMedia
    thumb: HWResizeMedia

class FeaturesMedia(BaseModel):
    """ TODO: Esto me dá posición de rostros en imágenes? turbio."""
    large: FacesMedia
    medium: FacesMedia
    small: FacesMedia
    orig: FacesMedia

class OneMedia(BaseModel):
    display_url: str
    expanded_url: str
    id_str: str
    indices: List[int]
    media_key: str
    media_url_https: str
    type: str
    url: str
    ext_media_availability: dict
    features: FeaturesMedia
    sizes: SizesMedia
    original_info: OriginalInfoMedia

class ExtendedEntities(BaseModel):
    media: List[OneMedia]