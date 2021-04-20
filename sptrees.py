import sys
import collections
import pygame
import math
import random
import scipy.spatial
import itertools

def bfs_forest(graph, root):
    t = [list() for _ in graph]
    t[root].append(-1)
    q = collections.deque([root])
    seen = set(q)
    while len(q) > 0:
        v = q.pop()
        for w in graph[v]:
            if w not in seen:
                seen.add(w)
                q.appendleft(w)
                t[w].append(v)  # sets w's parent to v
                t[v].append(w)  # makes w a child of v
    for i in range(len(t)):
        if not t[i]:
            t[i].append(-1)
    return t

def depth(v, t):
    d = 0
    while t[v][0] >= 0:
        d += 1
        v = t[v][0]
    return d

def distance_squared(p1, p2):
    x = p1[0]-p2[0]
    y = p1[1]-p2[1]
    return x**2 + y**2

class App(object):
    NORMAL_STATE, EDGE_DRAWING = 1, 2

    def __init__(self):
        pygame.init()
        self.size = (1024, 1024)
        self.screen = pygame.display.set_mode(self.size)
        self.font = pygame.font.SysFont(None, 20)

        self.state = App.NORMAL_STATE

        self.init_defaults()

    def init_defaults(self):
        self.vertex_positions = list()
        self.graph = list()
        self.t = list()
        self.root = 0
        self.root2 = 0

    def save_graph(self, filename):
        with open(filename, "w") as fp:
            for i in range(len(self.graph)):
                vline = [str(w) for w in self.graph[i]]
                vline += [str(x) for x in self.vertex_positions[i]]
                fp.write(" ".join(vline))
                fp.write("\n")

    def load_graph(self, filename):
        print("Loading file {}".format(filename))
        self.vertex_positions = list()
        self.graph = list()
        lines = open(filename).read().splitlines()
        for line in lines:
            ints = [int(x) for x in line.split()]
            self.graph.append(ints[:-2])
            self.vertex_positions.append(ints[-2:])

        for i in range(len(self.graph)):
            self.sort_neighbours(i)
        self.t = bfs_forest(self.graph, self.root)
        self.redraw()

    def set_graph(self, graph, vertex_positions):
        self.graph = graph
        self.vertex_positions = vertex_positions
        for i in range(len(self.graph)):
            self.sort_neighbours(i)
        self.t = bfs_forest(self.graph, self.root)
        self.redraw()

    def sort_neighbours(self, i):
        posi = self.vertex_positions[i]
        cmpi = lambda j: math.atan2(self.vertex_positions[j][1]-posi[1],                                      self.vertex_positions[j][0]-posi[0])
        self.graph[i].sort(key=cmpi)

    def run(self):
        while 1 < 2:
            event = pygame.event.wait()

            if event.type == pygame.QUIT \
                or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                break

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                v = self.nearest_vertex(event.pos)
                if v is None:
                    self.graph.append(list())
                    self.vertex_positions.append(event.pos)
                    self.t = bfs_forest(self.graph, self.root)
                    self.redraw()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
                print(event)
                r = self.nearest_vertex(event.pos)
                if r is not None:
                    if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        self.root2 = r
                        print("Setting second root {}".format(self.root2))
                    else:
                        self.root = r
                        self.t = bfs_forest(self.graph, self.root)
                    self.redraw()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if self.state == App.NORMAL_STATE:
                    self.s = self.nearest_vertex(event.pos)
                    if self.s is not None:
                        self.state = App.EDGE_DRAWING
                        self.redraw()
                elif self.state == App.EDGE_DRAWING:
                    t = self.nearest_vertex(event.pos)
                    if t is not None:
                        print("Adding edge ({},{})".format(self.s, t))
                        self.state = App.NORMAL_STATE
                        if t not in self.graph[self.s]:
                            self.graph[self.s].append(t)
                            self.graph[t].append(self.s)
                            self.sort_neighbours(self.s)
                            self.sort_neighbours(t)
                            self.s = None
                            self.t = bfs_forest(self.graph, self.root)
                        self.redraw()

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                filename = "graph.txt"
                print("Saving graph to {}".format(filename))
                self.save_graph(filename)

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                print("Clearing graph")
                self.init_defaults()
                self.redraw()



    def nearest_vertex(self, pos):
        v = None
        for i in range(len(self.vertex_positions)):
            if (v is None \
                or distance_squared(pos, self.vertex_positions[i]) \
                    < distance_squared(pos, self.vertex_positions[v])) \
                and distance_squared(pos, self.vertex_positions[i]) < 200:
                v = i
        return v


    def redraw(self):
        self.draw()
        pygame.display.flip()

    def draw(self):
        vertex_colour = (0, 0, 0)
        root_colour = (255, 0, 0)
        root2_colour = (0, 128, 255)
        edge_colour = vertex_colour
        tree_colour = (0, 255, 0)
        bg_colour = (255, 255, 255)
        self.screen.fill(bg_colour)

        if self.state == App.EDGE_DRAWING:
            pygame.draw.circle(self.screen, (255,0,0), self.vertex_positions[self.s], 10)

        for i in range(len(self.t)):
            for j in self.t[i][1:]:
                pi = self.vertex_positions[i]
                pj = self.vertex_positions[j]
                pygame.draw.line(self.screen, (255,128,0), pi, pj, 4)


        # Draw all the edges of self.graph
        for i in range(len(self.graph)):
            for j in self.graph[i]:
                pi = self.vertex_positions[i]
                pj = self.vertex_positions[j]
                pygame.draw.line(self.screen, edge_colour, pi, pj, 1)


        # Colour the vertices based on distance difference between t and t2
        t2 = bfs_forest(self.graph, self.root2)
        diffs = [depth(i, self.t)-depth(i, t2) for i in range(len(self.graph))]
        mindiff = min(diffs)
        maxdiff = max(diffs)
        diffscale = 127/(max(1,maxdiff,-mindiff))
        vertex_colours = list()
        for i in range(len(self.graph)):
            # if diffs[i] < 0:
            #     vertex_colours.append((128-diffscale*diffs[i], 0, 0))
            # elif diffs[i] > 0:
            #     vertex_colours.append((0, 128+diffscale*diffs[i], 0))
            # else:
            #      vertex_colours.append((0, 128, 255))
            vertex_colours.append((128-diffscale*diffs[i], 128+diffscale*diffs[i], 0))

        for i in range(len(self.vertex_positions)):
            pos = self.vertex_positions[i]
            if i == self.root or i == self.root2:
                radius = 10
            else:
                radius = 5
            colour = vertex_colours[i]
            pygame.draw.circle(self.screen, colour, pos, radius)
            if len(self.graph) <= 100:
                txt = str(depth(i, self.t))  # Warning: Quadratic time
                text = self.font.render(txt, True, (255, 128, 0))
                rect = text.get_rect()
                rect = rect.move(pos[0]-text.get_width(),
                                pos[1]-text.get_height())
                self.screen.blit(text, rect)
                if (self.root != self.root2):
                    txt = str(diffs[i])
                    text = self.font.render(txt, True, colour)
                    rect = text.get_rect()
                    rect = rect.move(pos[0], pos[1])
                    self.screen.blit(text, rect)



########
# Code borrowed from lhp_demo.py
########
def make_triangulation(n, data_type):
    print("Generating points")
    points = [random_point() for _ in range(n)]
    print("Computing Delaunay triangulation")
    graph = triangulate(points)
    return graph, points

""" Generate a random point in the unit circle """
def random_point():
    while 1 < 2:
        x = 2*random.random()-1
        y = 2*random.random()-1
        if x**2 + y**2 < 1:
            return (x, y)

def triangulate(points):
    n = len(points)
    dt = scipy.spatial.Delaunay(points)
    assert(dt.npoints == n)
    # assert(len(dt.convex_hull) == 3)
    # assert(dt.nsimplex == 2*n - 5)
    graph = [set() for _ in range(n)]
    for t in dt.simplices:
        for i in range(3):
            graph[t[i]].add(t[(i+1)%3])
            graph[t[(i+1)%3]].add(t[i])

    return [list(al) for al in graph]




if __name__ == "__main__":
    app = App()
    if len(sys.argv) == 2:
        app.load_graph(sys.argv[1])
    else:
        n = 5000
        graph, points = make_triangulation(n, 0)
        a = min([min(p) for p in points])
        b = max([max(p) for p in points])
        scale = (app.size[0]-50)/(b-a)
        vertex_positions = [(25+int((p[0]-a)*scale), 25+int((p[1]-a)*scale)) for p in points]
        app.set_graph(graph, vertex_positions)
        # print(app.vertex_positions)
    print("Running app")
    app.run()
