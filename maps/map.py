from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Type

Color = Tuple[int, int, int]


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
	stats: BlockStats = BlockStats("void", (255, 0, 255), False, 0.0)

	def __init__(self) -> None:
		pass

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

	def draw(self, surface, rect) -> None:
		import pygame

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
	symbol = "~"
	stats = BlockStats(
		"water",
		(28, 107, 160),
		False,
		0.2,
		speed_modifier=0.5,
		slows_projectiles=True,
	)


BLOCK_REGISTRY: Dict[str, Type[Block]] = {
	AirBlock.symbol: AirBlock,
	" ": AirBlock,
	EarthBlock.symbol: EarthBlock,
	StoneBlock.symbol: StoneBlock,
	RockBlock.symbol: RockBlock,
	WaterBlock.symbol: WaterBlock,
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

		return cls(rows, tile_size, spawn_points)

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
		return self.rows[row][col].block

	def is_solid_at(self, x: float, y: float) -> bool:
		block = self.block_at_pixel(x, y)
		return bool(block and block.solid)

	def get_spawn_point(self, index: int = 0) -> Tuple[int, int]:
		if not self.spawn_points:
			raise ValueError("Map does not define spawn points (use 'S' in the layout)")
		idx = max(0, min(index, len(self.spawn_points) - 1))
		return self.spawn_points[idx]

	def draw(self, surface) -> None:
		import pygame

		tile = self.tile_size
		for row_idx, row in enumerate(self.rows):
			y = row_idx * tile
			for col_idx, cell in enumerate(row):
				color = cell.block.color
				if color is None:
					continue
				rect = pygame.Rect(col_idx * tile, y, tile, tile)
				cell.block.draw(surface, rect)

	@staticmethod
	def _cell_center(col: int, row: int, tile_size: int) -> Tuple[int, int]:
		cx = col * tile_size + tile_size // 2
		cy = row * tile_size + tile_size // 2
		return cx, cy


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
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

# ### 1. Définition des Blocs (Classes Block et BlockStats)
#
# * **BlockStats (dataclass):** Une classe de données immuable (frozen=True) qui stocke toutes les
#   propriétés physiques et visuelles d'un type de bloc (nom, couleur, solidité, densité,
#   modificateurs de vitesse, etc.).
# * **Block (Classe de base):** La classe parente pour tous les types de blocs.
#     * Chaque sous-classe de Block (ex: AirBlock, EarthBlock, WaterBlock) définit son propre symbole
#       ASCII et ses stats spécifiques.
#     * Elle expose les propriétés des stats (color, solid, density, etc.) comme des attributs
#       directs pour une lecture facile.
#     * La méthode draw gère le rendu visuel du bloc (ici, en utilisant Pygame pour dessiner un
#       rectangle de couleur).
# * **BLOCK_REGISTRY:** Un dictionnaire global qui mappe chaque symbole ASCII (., #, X, ~) à sa
#   classe Block correspondante. C'est le cœur de la conversion du layout ASCII en objets réels.
#
# ### 2. Chargement du Layout (ASCII layout helpers)
#
# * **load_ascii_layout(path):** Lit un fichier texte, supprime les lignes vides, et renvoie une
#   liste de chaînes (lignes de la carte). Elle vérifie également que toutes les lignes ont la même
#   longueur pour garantir une grille rectangulaire.
# * **normalize_layout(layout):** Assure qu'un layout donné a une largeur uniforme, en complétant
#   avec des espaces si nécessaire.
#
# ### 3. Représentation de la Carte (GridMap)
#
# * **Cell (dataclass):** Une simple enveloppe autour d'une instance de Block, représentant une
#   seule position (tuile) dans la grille.
# * **GridMap:** La classe principale gérant la carte complète.
#     * rows: La grille de carte elle-même, stockée comme une liste de listes d'objets Cell.
#     * tile_size: La taille en pixels d'une seule tuile.
#     * spawn_points: Liste des coordonnées pixel des points d'apparition (S dans le layout).
#     * from_layout(layout): Méthode clé pour construire la carte. Elle itère sur le layout ASCII,
#       utilise le BLOCK_REGISTRY pour créer l'instance Block correcte pour chaque symbole, et
#       l'ajoute à la grille de Cell. Elle identifie et enregistre également les points
#       d'apparition.
#     * from_txt(path): Combine load_ascii_layout et from_layout pour charger la carte directement
#       depuis un fichier.
#     * Méthodes d'accès:
#         * block_at_pixel(x, y) et is_solid_at(x, y) : Permettent de déterminer quel bloc se trouve
#           à une coordonnée pixel donnée (utilisé pour la collision et l'interaction).
#         * height_at(x) : Calcule la hauteur du premier bloc solide dans une colonne, utile pour les
#           systèmes de gravité et de sol.
#     * draw(surface): Dessine chaque bloc de la grille sur la surface de rendu fournie.
#
# 
# 
# Le module établit une séparation claire entre la **définition des types de blocs** 
# (leurs propriétés physiques et visuelles) et la **structure de la carte** (la grille de blocs). Cela rend l'ajout de nouveaux 
# types de blocs facile et permet de charger rapidement des niveaux complexes à partir de simples fichiers texte.



