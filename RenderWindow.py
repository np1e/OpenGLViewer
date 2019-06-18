"""
/*******************************************************************************
 *
 *            #, #,         CCCCCC  VV    VV MM      MM RRRRRRR
 *           %  %(  #%%#   CC    CC VV    VV MMM    MMM RR    RR
 *           %    %## #    CC        V    V  MM M  M MM RR    RR
 *            ,%      %    CC        VV  VV  MM  MM  MM RRRRRR
 *            (%      %,   CC    CC   VVVV   MM      MM RR   RR
 *              #%    %*    CCCCCC     VV    MM      MM RR    RR
 *             .%    %/
 *                (%.      Computer Vision & Mixed Reality Group
 *
 ******************************************************************************/
/**          @copyright:   Hochschule RheinMain,
 *                         University of Applied Sciences
 *              @author:   Prof. Dr. Ulrich Schwanecke
 *             @version:   0.9
 *                @date:   03.06.2019
 ******************************************************************************/
/**         RenderWindow.py
 *
 *          Simple Python OpenGL program that uses PyOpenGL + GLFW to get an
 *          OpenGL 3.2 context and display some 2D animation.
 ****
"""

import sys, os

import glfw
from OpenGL.GL import *
from OpenGL.arrays import vbo
from OpenGL.GLU import *
from OpenGL.GLUT import *

from enum import Enum

import numpy as np
from numpy import array
from functools import reduce


class Scene:
    """ OpenGL 2D scene class """
    # initialization
    def __init__(self, width, height, points, normals, data, bbox):
        # time
        self.points = points
        self.normals = normals
        self.uni_vbo = vbo.VBO(array(data, "f"))
        self.vbo = vbo.VBO(array(self.points, "f"))
        self.vbon = vbo.VBO(array(self.normals, "f"))
        self.bbox = bbox
        self.center = [(x[0] + x[1]) / 2 for x in zip(*bbox)]
        self.t = 0
        self.point  = np.array([0,0])
        self.vector = np.array([10,10])
        self.pointsize = 3
        self.width = width
        self.height = height

        self.bgColor = [1., 1., 1., 1.]

        # arcball
        self.angle = 0
        self.axis = array([0,1,0])
        self.actOri = np.identity(4)
        self.doRotation = False

        #  zoom
        self.actSize = np.identity(4)
        self.doZoom = False
        self.scale = 1

        # move
        self.doTranslate = False
        self.offset = (0, 0)
        self.actPos = np.identity(4)

        # light
        self.xLight = 2400.0
        self.yLight = 3000.0
        self.zLight = 2400.0
        self.light = [self.xLight, self.yLight, self.zLight]

        # shadow
        self.shadowc = [0.3, 0.3, 0.3]
        self.doShadow = False
        self.shadow_p = [1.0, 0, 0, 0,
                         0, 1.0, 0, -1.0 / self.yLight,
                         0, 0, 1.0, 0,
                         0, 0, 0, 0]
        self.neg_y = min([b[1] for b in self.bbox])

        self.color = [0.1, 0.5, 0.8, 1.0]
        glPointSize(self.pointsize)
        glLineWidth(self.pointsize)

    # step
    def step(self):
        angle = 2
        axis = [0,1,0]
        glTranslate(self.center[0], self.center[1], self.center[2])
        glRotate(angle, *axis)
        glTranslate(-self.center[0], -self.center[1], -self.center[2])
        self.render()


    def rotate(self, angle, axis):
        angle *= 2
        c, mc = np.cos(angle), 1 - np.cos(angle)
        s = np.sin(angle)
        l = np.sqrt(np.dot(axis, axis))
        x, y, z = array(axis) / l
        r = np.matrix(
            [[x*x*mc+c, x*y*mc-z*s, x*z*mc+y*s, 0],
             [x*y*mc+z*s, y*y*mc+c, y*z*mc-x*s, 0],
             [x*z*mc-y*s, y*z*mc+x*s, z*z*mc+c, 0],
             [0, 0, 0, 1]])
        return r.T

    def zoom(self, factor):
        s = np.matrix(
            [[factor, 0, 0, 0],
             [0, factor, 0, 0],
             [0, 0, factor, 0],
             [0, 0, 0, 1]])
        return s

    def translate(self, tX, tY):
        t = np.matrix(
            [[1, 0, 0, tX],
             [0, 1, 0, tY],
             [0, 0, 1, 0],
             [0, 0, 0, 1]])
        return t.T

    # render 
    def render(self):

        glClearColor(*self.bgColor)
        mat_specular = [0.8, 0.8, 0.8, 0.5]
        mat_shininess = [8.0]
        glMaterialfv(GL_FRONT, GL_DIFFUSE, self.color)
        glMaterialfv(GL_FRONT, GL_SPECULAR, mat_specular)
        glMaterialfv(GL_FRONT, GL_SHININESS, mat_shininess)

        #self.vbo.bind()
        self.uni_vbo.bind()

        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_VERTEX_ARRAY)

        glVertexPointer(3, GL_FLOAT, 24, self.uni_vbo)

        if self.doShadow:
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            #glLoadIdentity()
            glTranslatef(0, self.neg_y, 0)

            glTranslatef(self.xLight, self.yLight, self.zLight)
            glMultMatrixf(self.shadow_p)
            glTranslatef(-self.xLight, -self.yLight, -self.zLight)
            glTranslatef(0, -self.neg_y, 0)
            glColor3f(self.shadowc[0], self.shadowc[1], self.shadowc[2])
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
            glDrawArrays(GL_TRIANGLES, 0, len(self.vbo))
            glPopMatrix()
            glEnable(GL_LIGHTING)
            glEnable(GL_DEPTH_TEST)

        glNormalPointer(GL_FLOAT, 24, self.uni_vbo+12)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # moving
        glMultMatrixf(self.actPos * self.translate(*self.offset))

        # scaling
        glMultMatrixf(self.actSize * self.zoom(self.scale))

        # rotation
        glMultMatrixf(self.actOri * self.rotate(self.angle, self.axis))

        #glScale(self.scale, self.scale, self.scale)
        glTranslate(-self.center[0], -self.center[1], -self.center[2])

        glDrawArrays(GL_TRIANGLES, 0, len(self.points))
        self.uni_vbo.unbind()
        #self.vbo.unbind()

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)


class ColorMode(Enum):
    background = 1
    object = 0

class RenderWindow:
    """GLFW Rendering window class"""
    def __init__(self, vertices, normals, data):

        glMatrixMode(GL_PROJECTION);
        glLoadIdentity();
        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity();
        
        # save current working directory
        cwd = os.getcwd()

        # Initialize the library
        if not glfw.init():
            return
        
        # restore cwd
        os.chdir(cwd)
        
        # version hints
        #glfw.WindowHint(glfw.CONTEXT_VERSION_MAJOR, 3)
        #glfw.WindowHint(glfw.CONTEXT_VERSION_MINOR, 3)
        #glfw.WindowHint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
        #glfw.WindowHint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        
        # buffer hints
        glfw.window_hint(glfw.DEPTH_BITS, 32)

        # define desired frame rate
        self.frame_rate = 100

        # make a window
        self.width, self.height = 900, 900
        self.aspect = self.width/float(self.height)
        self.window = glfw.create_window(self.width, self.height, "2D Graphics", None, None)
        self.ortho = False
        if not self.window:
            glfw.terminate()
            return

        # Make the window's context current
        glfw.make_context_current(self.window)

        glMatrixMode(GL_PROJECTION)

        self.setCamera()

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_FOG)

        glLightfv(GL_LIGHT0, GL_POSITION, [0., 0., 10., 0.])
        glLightfv(GL_LIGHT1, GL_AMBIENT, GLfloat_4(.1, .1, .1, 1.))
        glLightfv(GL_LIGHT1, GL_SPECULAR, GLfloat_4(1., 1.1, 1., 1.))
        glLightfv(GL_LIGHT1, GL_DIFFUSE, GLfloat_3(1., 1.0, 1.0))
        glLightfv(GL_LIGHT1, GL_POSITION, GLfloat_4(8, 1, 8, 0))

        boundingBox = [list(map(min, zip(*vertices))), list(map(max, zip(*vertices)))]

        # create 3D
        self.scene = Scene(self.width, self.height, vertices, normals, data, boundingBox)

        self.scene.center = [(x[0] + x[1]) / 2 for x in zip(*boundingBox)]
        self.scene.scale = 2. / max([x[1] - x[0] for x in zip(*boundingBox)])

        # move object to origin
        #glMatrixMode(GL_MODELVIEW)
        #glLoadIdentity()
        #glScale(self.scene.scale, self.scene.scale, self.scene.scale)
        #glTranslate(-self.scene.center[0], -self.scene.center[1] - boundingBox[1][1], -self.scene.center[2])

        # set window callbacks
        glfw.set_mouse_button_callback(self.window, self.onMouseButton)
        glfw.set_key_callback(self.window, self.onKeyboard)
        glfw.set_cursor_pos_callback(self.window, self.mouseMoved)
        #glfw.set_scroll_callback(self.window, self.scrolled)
        glfw.set_window_size_callback(self.window, self.onSize)
        
        # exit flag
        self.exitNow = False

        # animation flag
        self.animation = True

        self.colorMode = ColorMode.background

        self.prevX = -1
        self.prevY = -1

        glMatrixMode(GL_MODELVIEW)

    def setCamera(self):

        glMatrixMode(GL_PROJECTION)

        # initialize GL
        glViewport(0, 0, self.width, self.height)

        glLoadIdentity()

        aspect = float(self.width) / self.height

        if aspect >= 1.0:
            if self.ortho:
                glOrtho(-1.5 * aspect, 1.5 * aspect,
                        -1.5, 1.5,
                        -100, 100)
            else:
                gluPerspective(45., aspect, 0.1, 100.)
                glTranslatef(0., 0., -4.)
        else:
            if self.ortho:
                glOrtho(-1.5, 1.5,
                        -1.5 / aspect, 1.5 / aspect,
                        -100, 100)
            else:
                gluPerspective(45. * float(self.height) / self.width, aspect, 0.1, 100.)
                glTranslatef(0., 0., -4.)

        glMatrixMode(GL_MODELVIEW)


    def mapToRange(self, x, fromRange, toRange):

        r = (toRange[1] - toRange[0]) / (fromRange[1] - fromRange[0])

        return (x - fromRange[0]) * r + toRange[0]

    def mouseMoved(self, win, x, y):

        if self.scene.doRotation:
            r = min(self.width, self.height) / 2.0
            self.moveP = self.projectOnSphere(x, y, r)
            self.scene.angle = np.arccos(min(1.0, np.dot(self.startP, self.moveP)))
            self.scene.axis = np.cross(self.startP, self.moveP)

        if self.scene.doZoom:

            delta = y - self.startZoom[1]

            if self.prevY > y and self.scene.scale > 0:
                self.scene.scale += abs(float(float(delta / self.scene.height*2)))
            if self.prevY <= y and self.scene.scale > 0:
                self.scene.scale -= abs(float(float(delta / self.scene.height*2)))

            if self.scene.scale <= 0.00015:
                self.scene.scale = 0.0002
            print(self.scene.scale)
            self.prevY = y
            #self.scene.scale = self.mapToRange(delta, (deltaMin, deltaMax), (0., 2.))

        if self.scene.doTranslate:
            moveX, moveY = self.startPoint[0] - x, self.startPoint[1] - y
            x = self.mapToRange(moveX, (0, self.width), (0., 1.5))
            y = self.mapToRange(moveY, (0, self.height), (0., 1.5))
            self.scene.offset = -x, y

        self.prevX, self.prevY = x, y

    def scrolled(self, win, xoffset, yoffset):
        print(yoffset)
        deltaMax, deltaMin = self.height, 0.
        self.scene.scaleFactor = self.mapToRange(yoffset, (deltaMin, deltaMax), (1., 4.))
        if yoffset == 0:
            self.scene.scale = 1

    def projectOnSphere(self, x, y, r):
        x, y = x - self.width / 2.0, self.height / 2.0 - y
        a = min(r * r, x ** 2 + y ** 2)
        z = np.sqrt(r * r - a)
        l = np.sqrt(x ** 2 + y ** 2 + z ** 2)
        return x / l, y / l, z / l

    def onMouseButton(self, win, button, action, mods):
        print("mouse button: ", win, button, action, mods)

        # rotate on left mouse button
        if button == glfw.MOUSE_BUTTON_LEFT:
            r = min(self.width, self.height) / 2.0
            if action == glfw.PRESS:
                self.scene.doRotation = True
                x, y = glfw.get_cursor_pos(win)
                self.startP = self.projectOnSphere(x, y, r)
            if action == glfw.RELEASE:
                self.scene.doRotation = False
                self.scene.actOri = self.scene.actOri*self.scene.rotate(self.scene.angle, self.scene.axis)
                self.scene.angle = 0

        # scale on middle mouse button
        if button == glfw.MOUSE_BUTTON_MIDDLE:
            print("zoom")
            if action == glfw.PRESS:
                self.scene.doZoom = True
                self.startZoom = glfw.get_cursor_pos(win)
                self.prevY = self.startZoom[1]
            if action == glfw.RELEASE:
                self.scene.doZoom = False
                self.scene.actSize = self.scene.actSize * self.scene.zoom(self.scene.scale)
                self.scene.scale = 1

        # translate on right mouse button
        if button == glfw.MOUSE_BUTTON_RIGHT:
            if action == glfw.PRESS:
                self.scene.doTranslate = True
                self.startPoint = glfw.get_cursor_pos(win)
            if action == glfw.RELEASE:
                self.scene.doTranslate = False
                self.scene.actPos = self.scene.actPos * self.scene.translate(*self.scene.offset)
                self.scene.offset = (0, 0)

    def onKeyboard(self, win, key, scancode, action, mods):
        print("keyboard: ", win, key, scancode, action, mods)
        if action == glfw.PRESS:
            # ESC to quit
            if key == glfw.KEY_ESCAPE:
                self.exitNow = True
            if key == glfw.KEY_A:
                # toggle animation
                self.animation = not self.animation
            if key == glfw.KEY_O:
                self.ortho = True
                self.setCamera()
                self.run()
            if key == glfw.KEY_P:
                self.ortho = False
                self.setCamera()
                self.run()
            if key == glfw.KEY_C:
                if self.colorMode == ColorMode.background:
                    self.colorMode = ColorMode.object
                else:
                    self.colorMode = ColorMode.background

            if self.colorMode == ColorMode.background:
                if key == glfw.KEY_R:
                    self.scene.bgColor = [0.8, 0.1, 0.1, 1.0]
                if key == glfw.KEY_G:
                    self.scene.bgColor = [0.1, 0.8, 0.5, 1.0]
                if key == glfw.KEY_B:
                    self.scene.bgColor = [0.1, 0.5, 0.8, 1.0]
                if key == glfw.KEY_W:
                    self.scene.bgColor = [1., 1., 1., 1.]
                if key == glfw.KEY_S:
                    self.scene.bgColor = [0., 0., 0., 1.]
            else:
                if key == glfw.KEY_R:
                    self.scene.color = [0.8, 0.1, 0.1, 1.0]
                if key == glfw.KEY_G:
                    self.scene.color = [0.1, 0.8, 0.5, 1.0]
                if key == glfw.KEY_B:
                    self.scene.color = [0.1, 0.5, 0.8, 1.0]
                if key == glfw.KEY_W:
                    self.scene.color = [1., 1., 1., 1.]
                if key == glfw.KEY_S:
                    self.scene.color = [0., 0., 0., 1.]
            angle = np.radians(360/16)
            if key == glfw.KEY_X:
                if action == glfw.PRESS:
                    self.scene.angle = angle
                    self.scene.axis = [1,0,0]
                    self.scene.actOri = self.scene.actOri * self.scene.rotate(angle, [1,0,0])
                if action == glfw.RELEASE:
                    self.scene.angle = 0
            if key == glfw.KEY_Y:
                if action == glfw.PRESS:
                    self.scene.angle = angle
                    self.scene.axis = [0, 1, 0]
                    self.scene.actOri = self.scene.actOri * self.scene.rotate(angle, [0, 1, 0])
                if action == glfw.RELEASE:
                    self.scene.angle = 0
            if key == glfw.KEY_Z:
                self.scene.angle = angle
                self.scene.axis = [0, 0, 1]
                self.scene.actOri = self.scene.actOri * self.scene.rotate(angle, [0, 0, 1])
                if action == glfw.RELEASE:
                    self.scene.actOri = self.scene.actOri * self.scene.rotate(angle, [0, 0, 1])
                    self.scene.angle = 0
            if key == glfw.KEY_H:
                self.scene.doShadow = not self.scene.doShadow


    def onSize(self, win, width, height):
        print("onsize: ", win, width, height)
        if height == 0:
            height = 1
        self.width = self.scene.width = width
        self.height = self.scene.height = height
        self.aspect = width/float(height)
        glViewport(0, 0, self.width, self.height)
        self.setCamera()

    def run(self):

        glfw.set_input_mode(self.window,glfw.STICKY_KEYS,GL_TRUE)
        glfw.set_time(0.0)
        t = 0.0
        while not glfw.window_should_close(self.window) and not self.exitNow:
            currT = glfw.get_time()
            if currT - t > 1.0 / self.frame_rate:
                # update time
                t = currT

                # clear
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

                self.scene.render()

                glfw.swap_buffers(self.window)
                # Poll for and process events
                glfw.poll_events()
        # end
        glfw.terminate()

def normalize(x):
    return x / np.linalg.norm(x)


def calcNormals(x, y, z):

    xy = normalize(y) - normalize(x)
    xz = normalize(z) - normalize(x)

    n = np.cross(xy, xz)

    return n



def read_file(filename):
    vertices = []
    normals = []
    textures = []
    points = []
    nls = []
    data = []
    vertex_normals = {}
    faces = []

    with open(filename) as file:
        for line in file:
            if line.startswith("vn"):
                x,y,z = line.strip("vn ").split()
                normals.append(np.array([x,y,z]).astype(float))
                continue
            if line.startswith("vt"):
                x,y = line.strip("vt ").split()
                textures.append(np.array([x,y,z]).astype(float))
                continue
            if line.startswith("v"):
                x,y,z = line.strip("v ").split()
                vertices.append(np.array([x,y,z]).astype(float))
                continue
            if line.startswith("f"):
                # f v/vt/vn v/vt/vn v/vt/vn
                x,y,z = line.strip("f ").split()
                if len(x.split("/")) == 1:
                    x = np.array([int(x),0,0])
                    y = np.array([int(y),0,0])
                    z = np.array([int(z),0,0])
                else:
                    x = np.array([int(x) if x else 0 for x in line.strip("f ").split()[0].split("/")])
                    y = np.array([int(x) if x else 0 for x in line.strip("f ").split()[1].split("/")])
                    z = np.array([int(x) if x else 0 for x in line.strip("f ").split()[2].split("/")])

                if x[2] != 0: # normals are given

                    vertex_normals[x[0]] = normals[x[2] - 1]
                    vertex_normals[y[0]] = normals[y[2] - 1]
                    vertex_normals[z[0]] = normals[z[2] - 1]

                else:

                    # calc normal for face
                    n = calcNormals(np.array(vertices[x[0] - 1]), np.array(vertices[y[0] - 1]), np.array(vertices[z[0] - 1]))

                    # if there already is a normal for a vertex, just add n to the existing normal
                    if vertex_normals.get(x[0], np.array(0)).any():
                        vertex_normals[x[0]] += normalize(n)
                    else:
                        vertex_normals[x[0]] = normalize(n)

                    if vertex_normals.get(y[0], np.array(0)).any():
                        vertex_normals[y[0]] += normalize(n)
                    else:
                        vertex_normals[y[0]] = normalize(n)

                    if vertex_normals.get(z[0], np.array(0)).any():
                        vertex_normals[z[0]] += normalize(n)
                    else:
                        vertex_normals[z[0]] = normalize(n)

                faces.append([x, y, z])
                continue


    for face in faces:
        for vertex in face:
            data.append(vertices[vertex[0] - 1])
            points.append(vertices[vertex[0] - 1])
            data.append(vertex_normals[vertex[0]])
            nls.append(vertex_normals[vertex[0]])

    return points, nls, data

# main() function
def main():
    print("Modelviewer")

    if len(sys.argv) != 2:
        print(os.path.basename(__file__), "objectPoints")
        sys.exit()



    rw = RenderWindow(*read_file(sys.argv[1]))
    rw.run()


# call main
if __name__ == '__main__':
    main()