# Gakusei (Japanese 学生 - student, explore life)
An Old School Go/Weiqi/Baduk playing program

# Project goals
It seems like in today's world where AI is taking over
and neural network based Go playing programs has become
a de-facto standard there's no place for an old school
implementation of the game of Go. This, however, is only
partially true because if we emphasize the implementation of
traditional algoritms like ladder solvers or influence
estimation it turns out to be an exciting domain on its own.
So my goal was to write a program similar to those we had in 80s.
It's not about playing strength, it's about pure fun of playing
around with simple heuristics like attack/defense, pattern matching
and some simple influence estimation.

# Inspiration
Probably one of the first publicly available Go playing programs
was <a href="https://archive.org/details/byte-magazine-1981-04/page/n101/mode/2up"> Wally</a>
by Jonathan K. Millen which has served as an inspiration for many developers,
for instance GnuGo's original implementation is based on ideas introduced in Wally.
Another notable attempt to implement somewhat an extended version of Wally was
a C implementation by Bill Newman.

# Playing strength
It's miserable, should be around 30kyu, however gakusei beats
GnuGo 1.2 (first release available for download) which has around
the same amount of knowledge.

# How to play?
Gakusei is a GTP engine, so you'll need <a href="https://github.com/SabakiHQ/Sabaki">Sabaki GUI</a>
to play with it, however running GTP commands just right in terminal is also possible.

# How it works?
There's no explicit documantation but the source code contains comments
regarding the most crucial parts, so it shouldn't be difficult to learn
about game rules implementation and heuristics.
