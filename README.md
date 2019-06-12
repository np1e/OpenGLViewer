# OpenGL Viewer

Displays triangle meshes given as indexed faceset in .obj format, using OpenGL.

### Getting Started

Clone the repo and execute the following via the command line:
```
pip3 install -r requirements.txt
```

Run with
```
python3 RenderWindow.py yourobject.obj
```

Negative indices in the faceset are currently not supported.

### Built With

* [glfw](https://www.glfw.org/) - The GUI toolkit used
* [PyOpenGL](http://pyopengl.sourceforge.net/) - The OpenGL binding for Python
* [numpy](https://www.numpy.org/) - Used for computations


