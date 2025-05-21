###############################################################################
#                                                                             #
#           GAKUSEI - An Old School Go/Weiqi/Baduk playing program            #
#                                                                             #
###############################################################################

import sys
import copy
import random
from copy import deepcopy

# GLOBAL CONSTANTS
NONE = -1                   # value of not initialized variable
EMPTY = 0                   # blanc board square value
BLACK = 1                   # value of board square occupied by black stone
WHITE = 2                   # value of board square occupied by white stone
FENCE = 3                   # offboard value
STONE = 4                   # any stone value, including EMPTY
SOLVE = 5                   # pattern response value
ESCAPE = 6                  # liberty mask value

# GLOBAL VARIABLES
width = NONE                # board width (9, 13, 19 or other)
board = [[]]                # board position, two dimensional array
side = NONE                 # side to move, either BLACK or WHITE
ko = [NONE, NONE]           # [col, row] Ko square, cannot set a stone on it
groups = []                 # black and white groups database
best_move = NONE            # best move after search

# PATTERN DATABASE          # "$" is SOLVE, "." is EMPTY, "X" = BLACK, "O" is WHITE, "?" is STONE, ~ is FENCE
patterns= [
  [
    [EMPTY, EMPTY, EMPTY],  # . . .
    [STONE, WHITE, SOLVE],  # ? O $  Block
    [EMPTY, STONE, BLACK],  # . ? X
  ],
  [
    [EMPTY, EMPTY, STONE],  # . . ?
    [EMPTY, WHITE, STONE],  # . O ?  Hane
    [SOLVE, BLACK, STONE],  # $ X ?
  ],
  [
    [WHITE, SOLVE, EMPTY],  # O $ .
    [WHITE, BLACK, EMPTY],  # O X .  Bend
    [STONE, STONE, EMPTY]   # ? ? .
  ],
  [
    [STONE, EMPTY, EMPTY],  # ? . .
    [WHITE, SOLVE, EMPTY],  # O $ .  Cut
    [BLACK, WHITE, STONE]   # X O ?
  ],
  [
    [STONE, STONE, STONE],  # ? ? ?
    [STONE, SOLVE, WHITE],  # ? $ O  Wedge
    [STONE, BLACK, STONE]   # ? X ?
  ],
  [
    [FENCE, FENCE, FENCE],  # ~ ~ ~
    [STONE, SOLVE, BLACK],  # ? $ X  Yose 1
    [STONE, WHITE, BLACK]   # ? O X
  ],
  [
    [FENCE, FENCE, FENCE],  # ~ ~ ~
    [STONE, SOLVE, BLACK],  # ? $ X  Yose 2
    [STONE, EMPTY, WHITE],  # ? ? O
  ],
  [
    [FENCE, FENCE, FENCE],  # ~ ~ ~
    [STONE, SOLVE, STONE],  # ? $ ?  Yose 3
    [BLACK, WHITE, WHITE],  # X O O
  ]
]

def init_board():
  '''
  Initializes board array of a given size with zeros,
  sets the side to move, resets a Ko square,
  clears groups database
  '''
  global board, side, ko, groups
  board = [[0 for _ in range(width)] for _ in range(width)]
  for row in range(width):
    for col in range(width):
      if row == 0 or row == width-1 or col == 0 or col == width-1:
        board[row][col] = FENCE
  side = BLACK
  ko = [NONE, NONE]
  groups = [[], []]

def print_board():
  '''
  Prints the board and game state to STDOUT,
  used for debugging and by GTP command "showboard"
  '''
  for row in range(width):
    for col in range(width):
      if col == 0 and row != 0 and row != width-1:
        rown = width-row-1
        print((' ' if rown < 10 else ''), rown, end=' ')
      if board[row][col] == FENCE: continue
      if col == ko[0] and row == ko[1]: print('#', end=' ')
      else: print(['.', 'X', 'O', '#'][board[row][col]], end=' ')
    if row < width-1: print()
  print('   ', 'A B C D E F G H J K L M N O P Q R S T'[:width*2-4])
  print('\n    Side to move:', ('BLACK' if side == 1 else 'WHITE'), file=sys.stderr)
  print()

def print_groups():
  '''
  Prints board group data structures
  '''
  print('    Black groups:')
  for group in groups[BLACK-1]: print('      ', group)
  print('\n    White groups:')
  for group in groups[WHITE-1]: print('      ', group)
  print()

def count(col, row, color, marks):
  '''
  Finds all stones of a given color connected to to the
  current stone at board[row][col], marks stones and liberties
  in a corresponding array which is essentially a helper board
  '''
  stone = board[row][col]
  if stone == FENCE: return
  if stone and (stone & color) and marks[row][col] == EMPTY:
    marks[row][col] = stone
    count(col+1, row, color, marks)
    count(col-1, row, color, marks)
    count(col, row+1, color, marks)
    count(col, row-1, color, marks)
  elif stone == EMPTY:
    marks[row][col] = ESCAPE

def add_stones(marks, color):
  '''
  Extracts stone/liberty coordinate pairs and stores them as group
  '''
  group = {'stones': [], 'liberties' :[]}
  for row in range(width):
    for col in range(width):
      stone = marks[row][col]
      if stone == FENCE or stone == EMPTY: continue
      if stone == ESCAPE: group['liberties'].append((col, row))
      else: group['stones'].append((col, row))
  return group

def make_group(col, row, color):
  '''
  Returns a group of a given color at col, row
  '''
  marks = [[EMPTY for _ in range(width)] for _ in range(width)]
  count(col, row, color, marks)
  return add_stones(marks, color)

def update_groups():
  '''
  Keeps track of BLACK and WHITE groups on board by
  maintaining coordinates of stones and their liberties
  '''
  global groups
  groups = [[], []]
  for row in range(width):
    for col in range(width):
      stone = board[row][col]
      if stone == FENCE or stone == EMPTY: continue

      if stone == BLACK:
        group = make_group(col, row, BLACK)
        if group not in groups[BLACK-1]: groups[BLACK-1].append(group)
      if stone == WHITE:
        group = make_group(col, row, WHITE)
        if group not in groups[WHITE-1]: groups[WHITE-1].append(group)

def is_clover(col, row):
  '''
  Returns color of clover shape surrounding current square
  or EMPTY if this is not a clover shape
  '''
  clover_color = -1
  other_color = -1
  for stone in [board[row][col+1], board[row][col-1], board[row+1][col], board[row-1][col]]:
    if stone == FENCE: continue
    if stone == EMPTY: return EMPTY
    if clover_color == -1:
      clover_color = stone
      other_color = (3-clover_color)
    elif stone == other_color: return EMPTY
  return clover_color

def is_suicide(col, row, color):
  '''
  Checks if the stone of a given color placed at col, row
  would result in group self capture, returns true if
  so and false otherwise
  '''
  suicide = False
  board[row][col] = color
  marks = [[EMPTY for _ in range(width)] for _ in range(width)]
  count(col, row, color, marks)
  group = add_stones(marks, color)
  if len(group['liberties']) == 0: suicide = True
  board[row][col] = EMPTY
  return suicide

def is_atari(col, row, color):
  '''
  Checks if the stone of a given color placed at col, row
  is in atari, returns true if so and false otherwise
  '''
  atari = False
  board[row][col] = color
  marks = [[EMPTY for _ in range(width)] for _ in range(width)]
  count(col, row, color, marks)
  group = add_stones(marks, color)
  if len(group['liberties']) == 1: atari = True
  board[row][col] = EMPTY
  return atari

def get_influence(col, row):
  '''
  Calculates influence at col, row -
  the less uncrowded part of the board is
  the bigger influence value is returned
  '''
  influence = 0
  try:
    if board[row][col]     == EMPTY: influence += 60
    if board[row][col+1]   == EMPTY: influence += 13
    if board[row][col-1]   == EMPTY: influence += 13
    if board[row][col+2]   == EMPTY: influence += 5
    if board[row][col-2]   == EMPTY: influence += 5
    if board[row][col+3]   == EMPTY: influence += 1
    if board[row][col-3]   == EMPTY: influence += 1
    if board[row+1][col]   == EMPTY: influence += 13
    if board[row+1][col+1] == EMPTY: influence += 6
    if board[row+1][col-1] == EMPTY: influence += 6
    if board[row+1][col+2] == EMPTY: influence += 2
    if board[row+1][col-2] == EMPTY: influence += 2
    if board[row-1][col]   == EMPTY: influence += 13
    if board[row-1][col+1] == EMPTY: influence += 6
    if board[row-1][col-1] == EMPTY: influence += 6
    if board[row-1][col+2] == EMPTY: influence += 2
    if board[row-1][col-2] == EMPTY: influence += 2
    if board[row+2][col]   == EMPTY: influence += 5
    if board[row+2][col+1] == EMPTY: influence += 1
    if board[row+2][col-1] == EMPTY: influence += 1
    if board[row+2][col+2] == EMPTY: influence += 1
    if board[row+2][col-2] == EMPTY: influence += 1
    if board[row-2][col]   == EMPTY: influence += 5
    if board[row-2][col+1] == EMPTY: influence += 1
    if board[row-2][col-1] == EMPTY: influence += 1
    if board[row-2][col+2] == EMPTY: influence += 1
    if board[row-2][col-2] == EMPTY: influence += 1
    if board[row+3][col]   == EMPTY: influence += 1
    if board[row-3][col]   == EMPTY: influence += 1
  except: pass
  return influence

def play(col, row, color):
  '''
  Sets stone of a given color at col, row,
  handles captures, sets new Ko square when needed.
  '''
  global ko, side
  ko = [NONE, NONE]
  board[row][col] = color
  update_groups()
  for group in groups[(3-color-1)]:
    if len(group['liberties']) == 0:
      if len(group['stones']) == 1 and is_clover(col, row) == (3-color):
        ko = group['stones'][0]
      for stone in group['stones']:
        board[stone[1]][stone[0]] = EMPTY
  side = (3-color)

def big_moves(color):
  '''
  Attempts to make a big move based on influence
  '''
  moves = []
  rows = list(range(width))
  cols = list(range(width))
  for row in range(width):
    for col in range(width):
      if board[row][col] == FENCE: continue
      if board[row][col] == EMPTY and (col, row) != ko and not is_suicide(col, row, color):
        urgency = calculate_urgency('big_move', get_influence(col, row), (col, row))
        if (col, row) in [(4,4), (4,width-5), (width-5,4), (width-5,width-5)]: urgency += 20
        if (col, row) in [(4,width//2), (width//2,4), (width-5,width//2), (width//2,width-5)]: urgency += 10
        if row == 3 or row == (width-4) or col == 3 or col == (width-4): urgency += 5
        if not is_atari(col, row, color):
          if not is_clover(col, row) != EMPTY:
            moves.append([(col, row), urgency, 'big_move'])
  moves.sort(key=lambda x: x[1], reverse=True)
  if len(moves): return [moves[0]]
  else: return []

def rotate_pattern(pattern):
  '''
  Returns a copy of a 90 degrees rotated pattern
  '''
  rotate = copy.deepcopy(pattern)
  return [[rotate[2 - j][i] for j in range(3)] for i in range(3)]

def swap_colors(pattern):
  '''
  Returns a copy of a pattern with black and white stones swapped
  '''
  swapped = copy.deepcopy(pattern)
  for row in range(3):
    for col in range(3):
      if swapped[row][col] == BLACK: swapped[row][col] = WHITE
      elif swapped[row][col] == WHITE: swapped[row][col] = BLACK
  return swapped

def make_patterns():
  '''
  Extends existing pattern database with patterns
  rotated into 4 directions with normal and swapped
  colors, returns the eventual pattern database to
  match board with
  '''
  all_patterns = []
  for pattern in patterns:
    for _ in range(4):
      pattern = rotate_pattern(pattern)
      swapped = swap_colors(pattern)
      for pat in [pattern, swapped]:
        all_patterns.append(pat)
  return all_patterns

def board_to_3x3_patterns():
  '''
  Returns board as a list of 3x3 patterns for matching purposes
  '''
  board_patterns = []
  blen = len(board)
  if blen < 3: raise ValueError("The array must be at least 3x3 in size.")
  for row in range(blen - 2):
    for col in range(blen - 2):
      board_patterns.append([(col, row), [prow[col:col+3] for prow in board[row:row+3]]])
  return board_patterns

def match_pattern(color):
  '''
  Returns a list of pattern matching moves on board
  '''
  pattern_moves = []
  for mpat in make_patterns():
    for bpat in board_to_3x3_patterns():
      is_match = True
      response = ()
      for row in range(3):
        for col in range(3):
          if mpat[row][col] == SOLVE:
            response = (bpat[0][0] + col, bpat[0][1] + row)
            if board[response[1]][response[0]] != EMPTY: is_match = False
          elif mpat[row][col] != SOLVE and mpat[row][col] != STONE:
            if mpat[row][col] != bpat[1][row][col]: is_match = False
      if is_match:
        urgency = calculate_urgency('pattern', mpat, response)
        if not is_suicide(response[0], response[1], color):
          if not is_atari(response[0], response[1], color):
            if not is_clover(response[0], response[1]):
              pattern_moves.append([response, urgency, 'pattern'])

  pattern_moves.sort(key=lambda x: x[1])
  return pattern_moves

def is_ladder(col, row, color, first_run):
  '''
  Resursively simulates a ladder chasing and
  figures out whether it works or not
  '''
  group = make_group(col, row, color)
  if len(group['liberties']) == 0: return 1
  if len(group['liberties']) == 1:
    if board[row][col] != EMPTY and first_run == False:
      if len(group['liberties']) <= 1: return 1
      else: return 0
    board[row][col] = color
    new_col = group['liberties'][0][0]
    new_row = group['liberties'][0][1]
    if is_ladder(new_col, new_row, color, False): return 1
    board[row][col] = EMPTY
  if len(group['liberties']) == 2:
    for move in group['liberties']:
      board[move[1]][move[0]] = (3-color)
      group = make_group(col, row, color)
      new_col = group['liberties'][0][0]
      new_row = group['liberties'][0][1]
      if is_ladder(new_col, new_row, color, False): return move
      board[move[1]][move[0]] = EMPTY
  return 0

def check_ladder(col, row, color):
  '''
  Return true if ladder is working and false otherwise,
  initial group to check should contain 2 liberties
  '''
  global board
  current_board = copy.deepcopy(board)
  ladder = is_ladder(col, row, color, True)
  board = copy.deepcopy(current_board)
  return ladder

def attack(group, color):
  '''
  Returns the best move to attack a given group
  '''
  moves = []
  surround_moves = []
  if len(group['liberties'])== 1: # capture group
    if group['liberties'][0] != ko:
      urgency = calculate_urgency('capture', group, group['liberties'][0])
      moves.append([group['liberties'][0], urgency, 'capture'])
  if len(group['liberties']) == 2: # check ladder attack
    stone = group['stones'][0]
    move = check_ladder(stone[0], stone[1], (3-color))
    if move:
      if not is_suicide(move[0], move[1], color):
        if not is_atari(move[0], move[1], color):
          urgency = calculate_urgency('ladder', group, move)
          moves.append([move, urgency, 'ladder_attack'])
  if len(moves):
    moves.sort(key=lambda x: x[1])
    return moves
  return []

def defend(group, color):
  '''
  Returns the best move to defend a given group
  '''
  moves = []
  extend_moves = []
  urgency = int(len(group['stones']) / len(group['liberties']))
  if len(group['liberties'])== 1: # save group
    if not is_suicide(group['liberties'][0][0], group['liberties'][0][1], color):
      urgency = calculate_urgency('save', group, group['liberties'][0])
      stone = group['stones'][0]
      ladder = check_ladder(stone[0], stone[1], color) # check if not trapped into a ladder
      if not ladder: moves.append([group['liberties'][0], urgency, 'save'])
  if len(extend_moves):
    extend_moves.sort(key=lambda x: x[1])
    moves.append(extend_moves[0])
  if len(moves):
    moves.sort(key=lambda x: x[1], reverse=True)
    return moves
  return []

def calculate_urgency(move_type, group, move):
  '''
  Returns urgency value based on group size
  and amount of its liberties, move type and location
  '''
  if move_type == 'big_move': return (width)+group
  elif move_type == 'pattern':
    center = (width // 4, width // 4)
    distance = abs(move[0] - center[0]) + abs(move[1] - center[1])
    weight = 0
    for row in group:
      for col in row: weight += col
    return (width*21)-distance+weight*4
  else:
    center = (width // 2, width // 2)
    distance = abs(move[0] - center[0]) + abs(move[1] - center[1])
    urgency = int(len(group['stones']) / len(group['liberties']))
    if move_type == 'capture': urgency += (width*37)
    elif move_type == 'ladder': urgency += (width*25)
    elif move_type == 'save': urgency += ((width*37)-distance)
    return urgency

def genmove(color):
  '''
  Returns list of moves sorted by its "urgency", it's
  used for move ordering within alpha beta search.
  '''
  
  update_groups()
  moves = []

  # Generate big move
  for move in big_moves(color):
    if move not in moves:
      moves.append(move)

  # Generate attacking moves
  for group in groups[(3-color-1)]: # attack opponent's weakest group
    for move in attack(group, color):
      if move != NONE and move not in moves:
        moves.append(move)
  
  # Generate defensive moves
  for group in groups[(color-1)]: # defend own weakest group
    for move in defend(group, color):
      if move != NONE and move not in moves:
        moves.append(move)
  
  # Generate pattern matches
  for move in match_pattern(color):
    if move not in moves:
      moves.append(move)
  
  # Sort moves in place by urgency in descending order
  if len(moves):
    moves.sort(key=lambda x: x[1], reverse=True)
    return unique(moves)[:-1] if len(moves) > 1 else moves
  return []

def unique(moves):
  '''
  Filters duplicate moves
  '''
  seen_tuples = set()
  unique = []
  for sublist in moves:
    tuples_in_sublist = {item for item in sublist if isinstance(item, tuple)}
    if tuples_in_sublist & seen_tuples: continue
    seen_tuples.update(tuples_in_sublist)
    unique.append(sublist)
  return unique

def root(depth, color):
  '''
  Root moves search
  '''
  global board, groups, side, ko, best_move
  best_score = -10000
  temp_best = NONE
  moves = genmove(side)
  for move in moves:
    old_board = deepcopy(board)
    old_groups = deepcopy(groups)
    old_side = side
    old_ko = ko
    if move != NONE: play(move[0][0], move[0][1], side)
    score = -negamax(depth-1, -10000, 10000)
    print('>', move_to_string(move[0]), move, -score if side == BLACK else score, file=sys.stderr)
    board = old_board
    groups = old_groups
    side = old_side
    ko = old_ko
    if score > best_score:
      best_score = score
      temp_best = move
  best_move = temp_best
  return best_score

def negamax(depth, alpha, beta):
  '''
  Recursive alpha beta search
  '''
  global board, groups, side, ko, best_move
  if depth == 0:
    score = evaluate()
    #print_board()
    #print(score)
    return score
  moves = genmove(side)
  if len(moves):
    for move in genmove(side):
      old_board = deepcopy(board)
      old_groups = deepcopy(groups)
      old_side = side
      old_ko = ko
      if move != NONE: play(move[0][0], move[0][1], side)
      score = -negamax(depth-1, -beta, -alpha)
      board = old_board
      groups = old_groups
      side = old_side
      ko = old_ko
      if score > alpha:
        if score >= beta: break
        alpha = score
        best_move = move
  best_move = NONE
  return alpha

def evaluate():
  '''
  Score position based on resulting influence
  '''
  score = 0
  for row in range(width):
    for col in range(width):
      if board[row][col] == BLACK: score += 60 + get_influence(col, row)
      if board[row][col] == WHITE: score -= 60 - get_influence(col, row)
  return score if side == BLACK else -score

def search(command):
  '''
  Find and make best move
  '''
  color = BLACK if command.split()[-1].upper() == 'B' else WHITE
  moves = [move_to_string(m[0]) for m in genmove(color)]
  best_score = root(5, color)
  if best_move != NONE:
    play(best_move[0][0], best_move[0][1], color)
    print('= ' + move_to_string(best_move[0]) + '\n')
    if move_to_string(best_move[0]) not in moves:
      print('ERROR MOVE', file=sys.stderr)
      sys.exit(1)
  else: print('= pass\n')

def move_to_string(move):
  '''
  Convert move coords to algebraic notation
  '''
  global width
  col = chr(move[0]-(1 if move[0]<=8 else 0)+ord('A'))
  row = str(width-move[1]-1)
  return col+row

def gtp():
  '''
  Go Text Protocol command loop
  '''
  global width, side, best_move
  while True:
    command = input()
    if 'name' in command: print('= Gakusei\n')
    elif 'protocol_version' in command: print('= 2\n');
    elif 'version' in command: print('=', 'by Code Monkey King\n')
    elif 'list_commands' in command: print('= protocol_version\n')
    elif 'boardsize' in command: width = int(command.split()[1])+2; print('=\n')
    elif 'clear_board' in command: init_board(); print('=\n')
    elif 'showboard' in command: print('= ', end=''); print_board()
    elif 'play' in command:
      if 'pass'.upper() not in command:
        params = command.split()
        color = BLACK if params[1] == 'B' else WHITE
        col = ord(params[2][0])-ord('A')+(1 if ord(params[2][0]) <= ord('H') else 0)
        row = width-int(params[2][1:])-1
        play(col, row, color)
        print('=\n')
      else:
        side = (3-side)
        ko = [NONE, NONE]
        print('=\n')
    elif 'genmove' in command: search(command)
    elif 'quit' in command: sys.exit()
    else: print('=\n') # skip currently unsupported commands

# MAIN
width=19+2;   # set board width + offboard squares
init_board(); # set up board
gtp()         # start GTP IO communication
