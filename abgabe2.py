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

import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.arrays import vbo
import sys, math, os

import numpy as np

class Vector:
    def __init__(self, x, y, z):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.vector = np.array([self.x, self.y, self.z])

class Point():
    def __init__(self, v, vt, vn):

        if v != False: self.v = Vector(v[1], v[2], v[3])
        else: self.v = False

        if vt != False: self.vt = Vector(vt[1], vt[2], vt[3])
        else: self.vt = False

        if vn != False: self.vn = Vector(vn[1], vn[2], vn[3])
        else: self.vn = False

class Polygon:
    def __init__(self, poly, splitted):
        # x coord
        self.a = self.calcPoint(poly[1], splitted)
        self.b = self.calcPoint(poly[2], splitted)
        self.c = self.calcPoint(poly[3], splitted)
        self.points = np.array([self.a, self.b, self.c])
        
    def calcPoint(self, c, splitted):
        # v, vn 
        if("//" in c):
            p = c.split("//")
            p = list(map(int, p))

            v = splitted[p[0]-1]
            vt = False
            vn = splitted[p[1]-1]
            return Point(v, vt, vn)

        # v, vt, vn 
        elif("/" in c):
            p = c.split("/")
            p = list(map(int, p))
            v = splitted[p[0]-1]
            vt = splitted[p[1]-1]
            vn = splitted[p[2]-1]
            return Point(v, vt, vn)
        # v 
        elif("/" not in c):
            v = splitted[int(c)-1]
            vn = False
            vt = False
            return Point(v, vt, vn)

class Scene:
    """ OpenGL 2D scene class """
    # initialization
    def __init__(self, width, height):
        # time
        self.t = 0
        self.showVector = True
        self.point  = np.array([10,12])
        self.vector = np.array([10,10])
        self.pointsize = 1
        self.width = width
        self.height = height
        glPointSize(self.pointsize)
        glLineWidth(self.pointsize)
        
        f = open("bunny.obj", "r")
        lines = f.readlines()
        splitted = [l.split() for l in lines]

        self.polygons = self.genPolygons(splitted)
        self.vbo = self.genVBO()
        self.vbon = self.genVBON()
        self.bb = self.genBB(splitted)    



    def genPolygons(self, splitted):

        f = []
        for e in splitted:
            if(len(e) > 1):
                if e[0].startswith("f"):
                    f.append(e)
                
        polygons = []
        for poly in f:
            polygons.append(Polygon(poly, splitted))
    
        return polygons

    def genBB(self, splitted): 
        p = []
        for e in splitted:
            if(len(e) > 1):
                if e[0] == ("v"):
                    p.append(e[1:])
                
        bb = [list(map(min,zip(*p))),list(map(max,zip(*p)))]
        return bb
        

    def genVBO(self):
        vbo_arr = []
        for polygon in self.polygons:
            vbo_arr.append([polygon.a.v.x, polygon.a.v.y, polygon.a.v.z])
            vbo_arr.append([polygon.b.v.x, polygon.b.v.y, polygon.b.v.z])
            vbo_arr.append([polygon.c.v.x, polygon.c.v.y, polygon.c.v.z])

        print(vbo_arr)

        return vbo.VBO(np.array(vbo_arr, "f"))

    def genVBON(self):
        vbon_arr = []
        for polygon in self.polygons:
            if polygon.a.vn == False or  polygon.b.vn == False or  polygon.c.vn == False :
                a,b,c = polygon.points
                #print(a,b,c)
            else:
                vbon_arr.append([polygon.a.vn.x, polygon.a.vn.y, polygon.a.vn.z])
                vbon_arr.append([polygon.b.vn.x, polygon.b.vn.y, polygon.b.vn.z])
                vbon_arr.append([polygon.c.vn.x, polygon.c.vn.y, polygon.c.vn.z])

        return vbo.VBO(np.array(vbon_arr, "f"))
    
    # render 
    def render(self):
        # render a point

        glClear(GL_COLOR_BUFFER_BIT) #clear screen
        glColor(0.0, 0.0, 1.0)       #render stuff
        
        self.vbo.bind()
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)

        glVertexPointerf(self.vbo)
        glNormalPointerf(self.vbon)


        #glColorPointer( 3 , GL_FLOAT, 20 , self.vbo+2)

        glDrawArrays(GL_TRIANGLES, 0, len(self.vbo))

        self.vbo.unbind()

        glDisableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glFlush()







class RenderWindow:

    """GLFW Rendering window class"""
    def __init__(self):
        
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
        self.width, self.height = 500, 500
        self.aspect = self.width/float(self.height)
        self.window = glfw.create_window(self.width, self.height, "2D Graphics", None, None)
        if not self.window:
            glfw.terminate()
            return

        # Make the window's context current
        glfw.make_context_current(self.window)
    
        # initialize GL

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        #glShadeModel(GL_FLAT)

        glClearColor(0,0,0,0)         #background color
        glMatrixMode(GL_PROJECTION)              #switch to projection matrix
        glLoadIdentity()                         #set to 1

        gluPerspective(45.,1.,0.1,100.)

        glTranslatef(0,0,-2)
        
        glMatrixMode(GL_MODELVIEW)               #switch to modelview matrix
        
        # set window callbacks
        glfw.set_mouse_button_callback(self.window, self.onMouseButton)
        glfw.set_key_callback(self.window, self.onKeyboard)
        glfw.set_window_size_callback(self.window, self.onSize)
        
        # create 3D
        self.scene = Scene(self.width, self.height)

        # exit flag
        self.exitNow = False

        # animation flag
        self.animation = True
    
    
    def onMouseButton(self, win, button, action, mods):
        print("mouse button: ", win, button, action, mods)
        if(action):
            pass
    

    def onKeyboard(self, win, key, scancode, action, mods):
        #print("keyboard: ", win, key, scancode, action, mods)
        #if action == glfw.PRESS:
        # ESC to quit
        if key == glfw.KEY_ESCAPE:
            self.exitNow = True
        if key == glfw.KEY_D:
            #rechts
            glRotatef(10,0,1,0)
            glMatrixMode(GL_MODELVIEW)  
        if key == glfw.KEY_A:
            #links  
            glRotatef(-10,0,1,0)
            glMatrixMode(GL_MODELVIEW)  
        if key == glfw.KEY_S:
            #links  
            glRotatef(10,1,0,0)
            glMatrixMode(GL_MODELVIEW)  
        if key == glfw.KEY_W:
            #links
            glRotatef(-10,1,0,0)
            glMatrixMode(GL_MODELVIEW)   


    def onSize(self, win, width, height):
        print("onsize: ", win, width, height)
        self.width = width
        self.height = height
        self.aspect = width/float(height)
        glViewport(0, 0, self.width, self.height)

    def run(self):
        # initializer timer
        glfw.set_input_mode(self.window,glfw.STICKY_KEYS,GL_TRUE)
        glfw.set_time(0.0)
        t = 0.0
        while not glfw.window_should_close(self.window) and not self.exitNow:
            # update every x seconds
            currT = glfw.get_time()
            if currT - t > 1.0/self.frame_rate:
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




# main() function
def main():
    print("Simple glfw render Window")    
    rw = RenderWindow()
    rw.run()


# call main
if __name__ == '__main__':
    main()