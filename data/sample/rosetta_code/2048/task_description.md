# 2048

Category:Puzzles
Category:Games

;Task:
Implement a 2D sliding block puzzle game where blocks with numbers are combined to add their values.

;Rules of the game:
:* &nbsp; The rules are that on each turn the player must choose a direction &nbsp; (up, down, left or right).
:* &nbsp; All tiles move as far as possible in that direction, some move more than others. 
:* &nbsp; Two adjacent tiles (in that direction only) with matching numbers combine into one bearing the sum of those numbers. 
:* &nbsp; A move is valid when at least one tile can be moved, including by combination. 
:* &nbsp; A new tile is spawned at the end of each turn at a randomly chosen empty square &nbsp; (if there is one). 
:* &nbsp; Most of the time, a new 2 is to be added, but occasionally (10% of the time), a 4.
:* &nbsp; To win, the player must create a tile with the number 2048. 
:* &nbsp; The player loses if no valid moves are possible.

The name comes from the popular open-source implementation of this game mechanic, [https://gabrielecirulli.github.io/2048/ 2048].

;Requirements:
* &nbsp; "Non-greedy" movement.&nbsp; The tiles that were created by combining other tiles should not be combined again during the same turn (move).&nbsp; That is to say, that moving the tile row of:

                [2][2][2][2] 

:: to the right should result in: 

                ......[4][4] 

:: and not:

                .........[8] 

* &nbsp; "Move direction priority".&nbsp; If more than one variant of combining is possible, move direction shall indicate which combination will take effect. &nbsp; For example, moving the tile row of:

                ...[2][2][2] 

:: to the right should result in:

                ......[2][4] 

:: and not:

                ......[4][2] 

* &nbsp; Check for valid moves. The player shouldn't be able to gain new tile by trying a move that doesn't change the board.
* &nbsp; Check for a win condition.
* &nbsp; Check for a lose condition.
