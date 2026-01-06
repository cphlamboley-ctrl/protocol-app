
from dataclasses import dataclass
from typing import List
@dataclass
class VIP: id:str; name:str; role:str=""; note:str=""
@dataclass
class Medalist: rank:int; name:str; nation:str=""; club:str=""
@dataclass
class Category: id:str; title:str; discipline:str=""; round:str=""; medalists:List[Medalist]|None=None
@dataclass
class PlanningItem: order:int; category_id:str
@dataclass
class Assignment: category_id:str; vip_ids:List[str]
