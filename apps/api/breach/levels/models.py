from pydantic import BaseModel, Field

# Component types with no attack surface of their own — pure pass-through
# nodes in the graph (an internet source, a queue). Anything else must be a
# key in game_map.yaml's component_types.
PASSTHROUGH_COMPONENT_TYPES = frozenset({"internet", "queue"})


class ComponentTypeDef(BaseModel):
    techniques: list[str] = Field(default_factory=list)


class CardDef(BaseModel):
    cost: int
    mitigations: list[str]


class GameMap(BaseModel):
    component_types: dict[str, ComponentTypeDef]
    cards: dict[str, CardDef]

    def known_component_types(self) -> frozenset[str]:
        return frozenset(self.component_types) | PASSTHROUGH_COMPONENT_TYPES

    def techniques_for(self, component_type: str) -> list[str]:
        type_def = self.component_types.get(component_type)
        return type_def.techniques if type_def else []


class Component(BaseModel):
    id: str
    type: str
    label: str
    public: bool = False
    asset: bool = False


class Level(BaseModel):
    id: str
    title: str
    brief: str
    threat_level: str
    budget: int
    components: list[Component]
    edges: list[tuple[str, str]]
    entry_points: list[str]
    cards_available: list[str]

    def component_ids(self) -> frozenset[str]:
        return frozenset(c.id for c in self.components)
