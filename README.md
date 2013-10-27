Spinsim
=======

Spinsim is a little program I wrote to help me understand the math involved in making [this](https://github.com/unlimitedbacon/Theta-Printer) work. Its probably not very interesting to most people, since all it does is draw lines on the screen. However, it lays the groundwork for modifying a RepRap firmware to work with a polar printer.

Requirements
------------
* Python 3+
* SFML and python-sfml
* gnuplot and [python-gnuplot](https://github.com/yuyichao/gnuplot-py)

Usage
-----
Click somewhere then click somewhere else. It will draw a line and plot some graphs. Very exciting, isn't it?

Graph Legend
------------
| Color | Cartesian | Bipolar   |
|-------|-----------|-----------|
| Blue  | Ideal X   | Ideal θ₁  |
| Pink  | Ideal Y   | Ideal θ₂  |
| Red   | Actual X  | Actual θ₁ |
| Green | Actual Y  | Actual θ₂ |
