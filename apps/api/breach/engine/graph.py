from ..levels.models import Level


def build_adjacency(level: Level) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {c.id: [] for c in level.components}
    for from_id, to_id in level.edges:
        adjacency[from_id].append(to_id)
    return adjacency


def enumerate_simple_paths(level: Level) -> list[list[str]]:
    """All simple (no repeated node) paths from each entry point to each
    asset component. Levels are small, so brute-force DFS is fine
    (HANDOFF §5.2)."""
    adjacency = build_adjacency(level)
    asset_ids = [c.id for c in level.components if c.asset]

    paths: list[list[str]] = []

    def dfs(node: str, target: str, visited: set[str], path: list[str]) -> None:
        if node == target:
            paths.append(list(path))
            return
        for neighbour in adjacency.get(node, []):
            if neighbour in visited:
                continue
            visited.add(neighbour)
            path.append(neighbour)
            dfs(neighbour, target, visited, path)
            path.pop()
            visited.remove(neighbour)

    for entry in level.entry_points:
        for asset_id in asset_ids:
            if entry == asset_id:
                continue
            dfs(entry, asset_id, {entry}, [entry])

    paths.sort()
    return paths
