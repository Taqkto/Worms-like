from __future__ import annotations

import pygame
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Type

# ---------------------------------------------------------------------------
# Configuration & Cache
# ---------------------------------------------------------------------------
Color = Tuple[int, int, int]

# Dictionnaire pour ne pas recharger l'image 1000 fois
TEXTURE_CACHE: Dict[str, pygame.Surface] = {}

ASSET_DIR = Path(__file__).resolve().parents[1] / "Assets" / "Blocks"
BLOCK_TEXTURES = {
    "dirt": ASSET_DIR / "dirt.png",
    "grass": ASSET_DIR / "grass.png",
    "stone": ASSET_DIR / "stone.png",
    "water": ASSET_DIR / "water.png",
    "rock": ASSET_DIR / "stone.png",
}


def get_texture(path: str | Path, size: int) -> pygame.Surface:
    """Charge une image, la redimensionne et la stocke en mémoire."""
    path_str = str(path)
    key = f"{path_str}_{size}"
    
    if key not in TEXTURE_CACHE:
        try:
            # charger l'image
            img = pygame.image.load(path_str)
            #si l'écran est déjà initialisé sinon on ignore
            if pygame.display.get_surface():
                img = img.convert_alpha()
            img = pygame.transform.scale(img, (size, size))
            TEXTURE_CACHE[key] = img
        except (FileNotFoundError, pygame.error):
            print(f"Texture manquante : {path}")
            # Texture de remplacement (rose moche )
            surf = pygame.Surface((size, size))
            surf.fill((255, 0, 255))
            TEXTURE_CACHE[key] = surf
            
    return TEXTURE_CACHE[key]


# ---------------------------------------------------------------------------
# Block definitions
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class BlockStats:
    name: str
    color: Color | None
    solid: bool
    density: float
    speed_modifier: float = 1.0
    slows_projectiles: bool = False


class Block:
    symbol: str = "?"
    # Stats par défaut (void)
    stats: BlockStats = BlockStats("void", (255, 0, 255), False, 0.0)

    def __init__(self) -> None:
        # L'image actuelle du bloc 
        self.image: pygame.Surface | None = None

    @property
    def color(self) -> Color | None:
        return self.stats.color

    @property
    def solid(self) -> bool:
        return self.stats.solid

    @property
    def density(self) -> float:
        return self.stats.density

    @property
    def speed_modifier(self) -> float:
        return self.stats.speed_modifier

    def set_texture(self, path: str | Path, tile_size: int) -> None:
        """Assigne une texture spécifique à ce bloc."""
        self.image = get_texture(path, tile_size)

    def draw(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        #  Priorité à la texture si elle existe
        if self.image:
            surface.blit(self.image, rect)
            return

        # Sinon, on dessine la couleur simple
        if self.color is None:
            return
        pygame.draw.rect(surface, self.color, rect)


class AirBlock(Block):
    symbol = "."
    stats = BlockStats("air", None, False, 0.0)


class EarthBlock(Block):
    symbol = "#"
    stats = BlockStats("earth", (139, 90, 43), True, 1.0)


class StoneBlock(Block):
    symbol = "X"
    stats = BlockStats("stone", (100, 100, 100), True, 2.2)


class RockBlock(Block):
    symbol = "P"
    stats = BlockStats("pierre", (85, 85, 110), True, 2.8)


class WaterBlock(Block):
    symbol = "W"
    stats = BlockStats(
        "water",
        (28, 107, 160),
        False,
        0.2,
        speed_modifier=0.5,
        slows_projectiles=True,
    )


class NoSpawnBlock(Block):
    symbol = "!"
    stats = BlockStats("no_spawn", None, False, 0.0)


BLOCK_REGISTRY: Dict[str, Type[Block]] = {
    AirBlock.symbol: AirBlock,
    " ": AirBlock,
    EarthBlock.symbol: EarthBlock,
    StoneBlock.symbol: StoneBlock,
    RockBlock.symbol: RockBlock,
    WaterBlock.symbol: WaterBlock,
    NoSpawnBlock.symbol: NoSpawnBlock,
}


# ---------------------------------------------------------------------------
# ASCII layout helpers
# ---------------------------------------------------------------------------
def load_ascii_layout(path: str | Path) -> List[str]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Map file not found: {file_path}")

    rows: List[str] = []
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip("\r")
        if not line:
            continue
        rows.append(line)

    if not rows:
        raise ValueError(f"Empty map file: {file_path}")

    width = len(rows[0])
    for idx, row in enumerate(rows, start=1):
        if len(row) != width:
            raise ValueError(
                f"Inconsistent row length in {file_path} (line {idx} has {len(row)} columns, expected {width})"
            )

    return rows


def normalize_layout(layout: Sequence[str], target_width: int | None = None) -> List[str]:
    if not layout:
        raise ValueError("Layout cannot be empty")

    width = target_width or len(layout[0])
    normalized: List[str] = []
    for row in layout:
        if len(row) > width:
            raise ValueError("Layout row longer than target width")
        normalized.append(row.ljust(width))
    return normalized


# ---------------------------------------------------------------------------
# Grid map representation
# ---------------------------------------------------------------------------
def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


@dataclass(slots=True)
class Cell:
    block: Block


class GridMap:
    def __init__(
            self,
            rows: List[List[Cell]],
            tile_size: int,
            spawn_points: List[Tuple[int, int]] | None = None,
    ) -> None:
        if not rows or not rows[0]:
            raise ValueError("Grid map requires at least one cell")

        self.rows = rows
        self.tile_size = tile_size
        self.spawn_points = spawn_points or []
        self.height = len(rows) * tile_size
        self.width = len(rows[0]) * tile_size

    @classmethod
    def from_layout(
            cls,
            layout: Sequence[str],
            tile_size: int = 32,
            registry: dict[str, Type[Block]] | None = None,
            spawn_symbol: str = "S",
    ) -> "GridMap":
        if not layout:
            raise ValueError("Layout cannot be empty")

        registry = registry or BLOCK_REGISTRY
        rows: List[List[Cell]] = []
        spawn_points: List[Tuple[int, int]] = []

        for row_idx, row in enumerate(layout):
            cells: List[Cell] = []
            for col_idx, symbol in enumerate(row):
                is_spawn = symbol == spawn_symbol
                if is_spawn:
                    symbol = "."

                block_cls = registry.get(symbol)
                if block_cls is None:

                    raise ValueError(
                        f"Unknown map symbol '{symbol}' at row {row_idx}, column {col_idx}"
                    )

                cell = Cell(block=block_cls())
                cells.append(cell)

                if is_spawn:
                    spawn_points.append(cls._cell_center(col_idx, row_idx, tile_size))
            rows.append(cells)

        # Création de l'instance
        grid_map = cls(rows, tile_size, spawn_points)
        
        # texture
        grid_map.apply_autotiling()
        
        return grid_map

    @classmethod
    def from_txt(
            cls,
            path: str | Path,
            tile_size: int = 32,
            registry: dict[str, Type[Block]] | None = None,
            spawn_symbol: str = "S",
    ) -> "GridMap":
        layout = load_ascii_layout(path)
        return cls.from_layout(
            layout,
            tile_size=tile_size,
            registry=registry,
            spawn_symbol=spawn_symbol,
        )

    def apply_autotiling(self) -> None:
        """
        Parcourt la grille pour assigner les bonnes images.
        C'est ici qu'on transforme la Terre en Herbe si elle touche l'air.
        """
        rows_count = len(self.rows)
        cols_count = len(self.rows[0])

        for y in range(rows_count):
            for x in range(cols_count):
                cell = self.rows[y][x]
                block = cell.block
                
                # --- Logique TERRE / HERBE ---
                if isinstance(block, EarthBlock):
                    # On regarde le bloc audessus
                    idx_above = y - 1
                    
                    is_top_exposed = False
                    
                    if idx_above < 0:
                        # C'est le tout haut de la map = exposé
                        is_top_exposed = True
                    else:
                        block_above = self.rows[idx_above][x].block
                        # Si le bloc au-dessus n'est PAS solide alors on met de l'herbe
                        if not block_above.solid:
                            is_top_exposed = True
                    
                    if is_top_exposed:
                        block.set_texture(BLOCK_TEXTURES["grass"], self.tile_size)
                    else:
                        block.set_texture(BLOCK_TEXTURES["dirt"], self.tile_size)

                # --- autres
                elif isinstance(block, StoneBlock):
                    block.set_texture(BLOCK_TEXTURES["stone"], self.tile_size)
                
                elif isinstance(block, RockBlock):
                    block.set_texture(BLOCK_TEXTURES["rock"], self.tile_size)
                    
                elif isinstance(block, WaterBlock):
                    block.set_texture(BLOCK_TEXTURES["water"], self.tile_size)

    # ---------------------------------------------------------------------------
    #  Méthodes existantes
    # ---------------------------------------------------------------------------
    def columns(self) -> int:
        return len(self.rows[0])

    def rows_count(self) -> int:
        return len(self.rows)

    def height_at(self, x: float) -> float:
        tile = self.tile_size
        col = int(clamp(x, 0, self.width - 1) // tile)
        for row_idx in range(self.rows_count()):
            cell = self.rows[row_idx][col]
            if cell.block.solid:
                return row_idx * tile
        return float(self.height)

    def block_at_pixel(self, x: float, y: float) -> Block | None:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return None
        tile = self.tile_size
        col = int(x) // tile
        row = int(y) // tile
        # Sécurité supplémentaire index error
        if row >= len(self.rows) or col >= len(self.rows[0]):
            return None
        return self.rows[row][col].block

    def is_solid_at(self, x: float, y: float) -> bool:
        block = self.block_at_pixel(x, y)
        return bool(block and block.solid)

    def random_spawn_point(self) -> Tuple[int, int]:
        import random
        tile = self.tile_size
        cols_with_ground: List[Tuple[int, int]] = []

        for col in range(self.columns()):
            #  vérif si la colonne contient un bloc anti-spawn
            has_no_spawn = False
            for r in range(self.rows_count()):
                if isinstance(self.rows[r][col].block, NoSpawnBlock):
                    has_no_spawn = True
                    break
            if has_no_spawn:
                continue

            #premier bloc solide en partant du haut
            first_solid_row = -1
            for row_idx in range(self.rows_count()):
                if self.rows[row_idx][col].block.solid:
                    first_solid_row = row_idx
                    break
            
            # Si on a trouvé un sol
            if first_solid_row != -1:
                # vérif qu'il n'y a pas d'eau au-dessus
                has_water_above = False
                for r in range(first_solid_row):
                    if isinstance(self.rows[r][col].block, WaterBlock):
                        has_water_above = True
                        break
                
                if not has_water_above:
                    cols_with_ground.append((col, first_solid_row))

        if not cols_with_ground:
            cx = self.width // 2
            cy = max(tile // 2, 0)
            return int(cx), int(cy)

        col, row_idx = random.choice(cols_with_ground)
        cx = col * tile + tile // 2
        top_solid_y = row_idx * tile
        cy = max(tile // 2, top_solid_y - tile // 2)
        return int(cx), int(cy)

    def destroy_circle(self, cx: float, cy: float, radius: float) -> None:
        """Creuse un trou dans la grille en remplaçant les blocs solides par de l'air."""
        if radius <= 0:
            return

        tile = self.tile_size
        r_sq = radius * radius
        min_col = max(0, int((cx - radius) // tile))
        max_col = min(self.columns() - 1, int((cx + radius) // tile))
        min_row = max(0, int((cy - radius) // tile))
        max_row = min(self.rows_count() - 1, int((cy + radius) // tile))

        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                block = self.rows[row][col].block
                if not block.solid:
                    continue

                # Harder blocks 
                resistance = 1.0
                if isinstance(block, (StoneBlock, RockBlock)):
                    resistance = 0.5

                eff_radius_sq = (radius * resistance) ** 2
                center_x = col * tile + tile / 2
                center_y = row * tile + tile / 2
                if (center_x - cx) ** 2 + (center_y - cy) ** 2 > eff_radius_sq:
                    continue

                self.rows[row][col] = Cell(block=AirBlock())

    def random_spawn_for_character(self, character_width: int) -> Tuple[int, None]:
        cx, _ = self.random_spawn_point()
        left_x = cx - (character_width // 2)
        max_left = max(0, self.width - character_width)
        left_x = int(clamp(float(left_x), 0.0, float(max_left)))
        return left_x, None

    def draw(self, surface) -> None:
        tile = self.tile_size
        
        for row_idx, row in enumerate(self.rows):
            y = row_idx * tile
            for col_idx, cell in enumerate(row):
                # Pas la peine de dessiner l'air invisible
                if isinstance(cell.block, AirBlock):
                    continue
                    
                rect = pygame.Rect(col_idx * tile, y, tile, tile)
                cell.block.draw(surface, rect)

    @staticmethod
    def _cell_center(col: int, row: int, tile_size: int) -> Tuple[int, int]:
        cx = col * tile_size + tile_size // 2
        cy = row * tile_size + tile_size // 2
        return cx, cy


DEFAULT_LAYOUT = Path(__file__).with_name("layouts").joinpath("default.txt")


def load_default_map(tile_size: int = 32) -> GridMap:
    layout = load_ascii_layout(DEFAULT_LAYOUT)
    return GridMap.from_layout(layout, tile_size=tile_size)


def load_map_from_txt(path: str | Path, tile_size: int = 32, registry=None) -> GridMap:
    layout = load_ascii_layout(path)
    reg = registry or BLOCK_REGISTRY
    return GridMap.from_layout(layout, tile_size=tile_size, registry=reg)


__all__ = [
    "Block",
    "GridMap",
    "BLOCK_REGISTRY",
    "load_default_map",
    "load_map_from_txt",
    "load_ascii_layout",
    "normalize_layout",
]
