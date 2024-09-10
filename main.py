from itertools import combinations

class Sudoku:
  groups: set['Group']
  
  squares: list[list['Square']]
  
  def __init__(self, puzzle_string: str):
    # initialize the board
    
    # initialize squares
    self.squares = [[Square(f"sq_{y+1}{x+1}") for x in range(9)] for y in range(9)]
    
    # initialize groups
    row_groups = [Group(set(self.squares[y]), f"row_{y+1}") for y in range(9)]
    col_groups = [Group(set(row[x] for row in self.squares), f"col_{x+1}") for x in range(9)]
      
    # nonet groups
    blo_groups = [
        [Group(
          set(item for row in self.squares[y:y+3] for item in row[x:x+3]),
          f"blo_{y + int(x/3) + 1}"
        ).setInterGroups(set(row_groups[y:y+3]) | set(col_groups[x:x+3]))
        for x in range(0, 9, 3)]
      for y in range(0, 9, 3)
    ]
    
    # load the puzzle
    for y, row_str in enumerate(puzzle_string.split('\n')):
      for x, square_str in enumerate(row_str):
        if square_str != ' ':
          self.squares[y][x].set_numbers((int(square_str),))
          self.squares[y][x].color = "\033[1;37m"
    
    self.groups = set(row_groups) | set(col_groups) | set([a for b in blo_groups for a in b])
  
  def __repr__(self) -> str:
    return '\n'.join(
      ''.join(sq.value() for sq in row)
      for row in self.squares
    )
  
  def __iter__(self):
    return self.groups.__iter__()
  
  def square_clouds(self) -> str:
    return '\n'.join(
      ''.join(f'{len(sq.possibilities())}' for sq in row)
      for row in self.squares
    )
  
  def hidden_tuples(self, tuple: int) -> None:
    for gr in self:
      for cl_tuple in combinations([cl for cl in gr.clouds if len(cl) == tuple], tuple):
        success = False
        
        hidden_squares: set[Cloud] = gr.squares.intersection(*cl_tuple)
        if len(hidden_squares) != tuple:
          continue
        
        for sq in [sq for sq in cl_tuple[0] if len(sq) >= tuple * 3]:
          for cl in [cl for cl in sq if cl not in cl_tuple]:
            sq.remove(cl)
            cl.remove(sq)
            success = True
            
        if success:
          print(f"Hidden {tuple}-tuple {gr} @ {' & '.join(sq.name for sq in hidden_squares)} = {' & '.join(str(cl.number) for cl in cl_tuple)}")
    
  def naked_tuples(self, tuple: int) -> None:
    for gr in self.groups:
      for sq_tuple in combinations([sq for sq in gr.squares if len(sq) == tuple * 3], tuple):
        
        naked_clouds: set[Cloud] = gr.cloud_set.intersection(*sq_tuple)
        if len(naked_clouds) != tuple:
          continue
        
        for cl in [cl for cl in naked_clouds if len(cl) > 2]:
          for sq in [sq for sq in cl if sq not in sq_tuple]:
            for cl2 in [cl2 for cl2 in sq if cl2 == cl]:
              sq.remove(cl2)
              cl2.remove(sq)
          
          print(f"Naked {tuple}-tuple {gr} @ {' & '.join(sq.name for sq in sq_tuple)} = {' & '.join(str(cl.number) for cl in naked_clouds)}")
  
  def intersection_removal(self) -> None:
    for gr in self.groups:
      for inter_group in gr.inter_groups:
        for i in [i for i in range(9) if gr.clouds[i] < inter_group.clouds[i]]:
          for sq in inter_group.clouds[i] - gr.clouds[i]:
            for cl in [cl for cl in sq if cl == gr.clouds[i]]:
              sq.remove(cl)
              cl.remove(sq)
          print(f"{gr} < {inter_group} for {i + 1}")
  
  def solved(self) -> bool:
    return all(gr.solved() for gr in self.groups)
      
  def solve(self) -> None:
    progress: str = ""
    while progress != self.square_clouds():
      
      while progress != self.square_clouds():
        progress = self.square_clouds()
        self.hidden_tuples(1)
        self.naked_tuples(1)
      
      self.intersection_removal()
      if progress != self.square_clouds():
        continue
      self.hidden_tuples(2)
      if progress != self.square_clouds():
        continue
      self.naked_tuples(2)
      if progress != self.square_clouds():
        continue
      self.hidden_tuples(3)
      if progress != self.square_clouds():
        continue
      self.naked_tuples(3)
      if progress != self.square_clouds():
        continue
      self.hidden_tuples(4)
      if progress != self.square_clouds():
        continue
      self.naked_tuples(4)
      if progress != self.square_clouds():
        continue
  
class Cloud:
  number: int
  
  group: 'Group'
  squares: set['Square']
  
  name: str
  
  def __init__(self, group: 'Group', number: int):
    self.number = number
    self.group = group
    self.name = f'{group.name}_{number}'
    
    # Add squares from group to cloud
    self.squares = set()
    for square in group.squares:
      self.squares.add(square)
      square.clouds.add(self)
      
  def __repr__(self) -> str:
    return self.name
  
  def __len__(self) -> int:
    return len(self.squares)
  
  def __iter__(self):
    return self.squares.__iter__()
  
  def __eq__(self, other):
    if isinstance(other, Cloud):
      return self.number == other.number
    return False
  
  def __hash__(self):
    return hash(self.name)
  
  def __and__(self, other: 'Cloud') -> set['Square']:
    return self.squares & other.squares
    
  def __sub__(self, other: 'Cloud') -> set['Square']:
    return self.squares - other.squares
  
  def __or__(self, other: 'Cloud') -> set['Square']:
    return self.squares | other.squares
  
  def __lt__(self, other: 'Cloud') -> set['Square']:
    return self.squares < other.squares
  
  def remove(self, square: 'Square') -> None:
    self.squares.remove(square)
  
  def solved(self) -> bool:
    return len(self.squares) == 1

class Group:
  clouds: list[Cloud]
  squares: set['Square']
  cloud_set: frozenset[Cloud]
  
  name: str
  
  inter_groups: set['Group']
  
  def __init__(self, squares: set['Square'], name: str):
    self.name = name
    
    self.squares = squares
    for square in squares:
      square.groups.add(self)
    
    self.inter_groups = set()
    
    # Initialize clouds
    self.clouds = [Cloud(self, i) for i in range(1, 10)]
    self.cloud_set = frozenset(self.clouds)
    
  def __repr__(self) -> str:
    return self.name
  
  def solved(self) -> bool:
    return all(cl.solved() for cl in self.clouds)
  
  def setInterGroups(self, inter_groups: set['Group']) -> 'Group':
    self.inter_groups = inter_groups
    
    for gr in inter_groups:
      gr.inter_groups.add(self)
    
    return self

class Square:
  groups: set[Group]
  clouds: set[Cloud]
  name: str
  color: str
  
  def __init__(self, name: str):
    self.name = name
    self.groups = set()
    self.clouds = set()
    self.color = '\033[96m'
  
  def __repr__(self) -> str:
    return self.name
  
  def __len__(self) -> int:
    return len(self.clouds)
  
  def __iter__(self):
    return self.clouds.__iter__()
  
  def __and__(self, other: 'Square | set[Cloud]') -> set[Cloud]:
    if isinstance(other, Square):
      return self.clouds & other.clouds
    return self.clouds & other
    
  def __sub__(self, other: 'Square') -> set[Cloud]:
    return self.clouds - other.clouds
  
  def __or__(self, other: 'Square') -> set[Cloud]:
    return self.clouds | other.clouds
  
  def __lt__(self, other: 'Square') -> set[Cloud]:
    return self.clouds < other.clouds
  
  def remove(self, cloud: 'Cloud') -> None:
    self.clouds.remove(cloud)
  
  def value(self) -> str:
    number: int
    for cl in self.clouds:
      number = cl.number
    return self.color + f'{number}' + '\033[0m' if len(self.clouds) == 3 else ' '
  
  def solved(self) -> bool:
    return len(self.clouds) == 1
  
  def set_numbers(self, numbers: set[int]) -> None:
    for gr in self.groups:
      other_squares = [sq for sq in gr.squares if sq is not self]
      for sq in other_squares:
        other_clouds = [cl for cl in sq.clouds if cl.number in numbers]
        for cl in other_clouds:
          cl.remove(sq)
          sq.remove(cl)
    
    remove_clouds = [cl for cl in self.clouds if cl.number not in numbers]
    for cl in remove_clouds:
      cl.remove(self)
      self.remove(cl)
  
  def possibilities(self) -> list[int]:
    poss: list[int] = list(set(cl.number for cl in self.clouds))
    poss.sort()
    return poss

if __name__ == '__main__':
  puzzle_string: str = open('puzzle.txt').read()
  sudoku: Sudoku = Sudoku(puzzle_string)
  sudoku.solve()
  print(sudoku)