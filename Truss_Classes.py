#region imports
import math
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from GraphicsView_App import RigidLink, RigidPivotPoint
#endregion

# ChatGPT helped write these updates, specifically calculating the 
# vertical loads and creating the new RollerPivotPoint graphic item.

#region Custom Graphic Items
class RollerPivotPoint(RigidPivotPoint):
    """
    Subclasses RigidPivotPoint to draw a roller joint (circle on ground)
    instead of a pinned triangle.
    """
    def __init__(self, ptX, ptY, pivotHeight, pivotWidth, parent=None, pen=None, brush=None, rotation=0, name='RollerPivotPoint'):
        super().__init__(ptX, ptY, pivotHeight, pivotWidth, parent, pen, brush, rotation, name)

    def paint(self, painter, option, widget=None):
        path = qtg.QPainterPath()
        radius = min(self.height, self.width) / 2
        
        # Draw roller circle
        rollerRect = qtc.QRectF(-radius, 0, 2*radius, 2*radius)
        path.addEllipse(rollerRect)

        if self.pen is not None:
            painter.setPen(self.pen)
        if self.brush is not None:
            painter.setBrush(self.brush)
        painter.drawPath(path)

        # Draw ground line and hatch
        x5 = -self.width
        x6 = self.width
        y4 = 2 * radius
        painter.drawLine(x5, y4, x6, y4)
        penOutline = qtg.QPen(qtc.Qt.NoPen)
        hatchbrush = qtg.QBrush(qtc.Qt.BDiagPattern)
        painter.setPen(penOutline)
        painter.setBrush(hatchbrush)
        support = qtc.QRectF(x5, y4, self.width*2, self.height/2)
        painter.drawRect(support)

        self.rect = qtc.QRectF(-self.width, -self.radius, self.width*2, self.height*2+self.radius)
        self.transformation.reset()
        self.transformation.translate(self.x, self.y)
        self.transformation.rotate(self.rotationAngle)
        self.setTransform(self.transformation)
#endregion

# ... (Keep Position, Rectangle, Material classes exactly as they were) ...

class Node():
    def __init__(self, name=None, position=None):
        self.name = name
        self.position = position if position is not None else Position()
        self.graphic = RigidPivotPoint(position.x, position.y, 10,30)
        self.reaction_y = 0.0 # $NEW$ Store vertical reaction load

    def __eq__(self, other):
        if self.name != other.name: return False
        if self.position != other.position: return False
        return True

class Link():
    def __init__(self,name="", node1="1", node2="2", length=None, angleRad=None, material="Steel", width=1.0, thickness=0.25):
        self.name=name
        self.node1_Name=node1
        self.node2_Name=node2
        self.length=None
        self.angleRad=None
        
        # $NEW$ Extra columns
        self.material = material
        self.width = width
        self.thickness = thickness
        self.weight = 0.0 
        
        self.graphic=RigidLink(0,0,1,1)
        self.graphic.name=name

    def __eq__(self, other):
        if self.node1_Name != other.node1_Name: return False
        if self.node2_Name != other.node2_Name: return False
        if self.length != other.length: return False
        if self.angleRad != other.angleRad: return False
        return True

    def set(self, node1=None, node2=None, length=None, angleRad=None):
        self.node1_Name=node1
        self.node2_Name=node2
        self.length=length
        self.angleRad=angleRad

# ... (Keep TrussModel exactly as it was) ...

class TrussView():
    # ... (Keep __init__, setDisplayWidgets, displayReport, buildScene, drawAGrid exactly as they were) ...

    def drawLinks(self, truss=None):
        scene = self.scene
        truss.getCenterPt()
        rct = truss.rct
        offset = Position(x=rct.centerX(), y=rct.centerY())

        penLink = self.penLink
        for l in truss.links:
            n1 = truss.getNode(l.node1_Name)
            n2 = truss.getNode(l.node2_Name)
            l.graphic = RigidLink(n1.position.x - offset.x, -(n1.position.y - offset.y), n2.position.x - offset.x,
                                  -(n2.position.y - offset.y), radius=3, pen=self.penLink, brush=self.brushLink, name="link name = "+l.name)
            
            # $NEW$ Enhanced Tooltip including weight
            st = f"link name = {l.name}\nstart ({n1.position.x:.3f}, {n1.position.y:.3f})\n" \
                 f"end ({n2.position.x:.3f}, {n2.position.y:.3f})\nlength {l.length:.3f}\n" \
                 f"angle {math.degrees(l.angleRad):.3f}\nweight {l.weight:.3f} lbs"
            
            l.graphic.setToolTip(st)
            scene.addItem(l.graphic)

    def drawNodes(self, truss=None, scene=None):
        truss.getCenterPt()
        rct = truss.rct
        offset = Position(x=rct.centerX(), y=rct.centerY())
        for n in truss.nodes:
            x = n.position.x - offset.x
            y = (n.position.y - offset.y)
            
            # $NEW$ Add Vertical Reaction to Tooltip
            toolTip = "Node: " + n.name
            if n.name.lower() in ['left', 'right']:
                 toolTip += f"\nVertical Load: {n.reaction_y:.2f} lbs"

            if n.name.lower() == 'left':
                n.graphic = RigidPivotPoint(x, -y, 10, 18, brush=self.brushPivot, name=n.name)
                n.graphic.setToolTip(toolTip)
                self.scene.addItem(n.graphic)
            elif n.name.lower() == 'right':
                # $NEW$ Roller joint at the right node
                n.graphic = RollerPivotPoint(x, -y, 10, 18, brush=self.brushPivot, name=n.name)
                n.graphic.setToolTip(toolTip)
                self.scene.addItem(n.graphic)
                
            self.drawALabel(x=x - 5, y=y + 15, str=n.name, pen=self.penLabel)

    # ... (Keep drawALabel and drawACircle exactly as they were) ...

class TrussController():
    def __init__(self):
        self.truss=TrussModel()
        self.view=TrussView()

    #region $NEW$ MVC Helper Methods
    def installSceneEventFilter(self, obj):
        self.view.scene.installEventFilter(obj)

    def isScene(self, obj):
        return obj == self.view.scene

    def getItemAt(self, pos, transform):
        return self.view.scene.itemAt(pos, transform)

    def getItemsAt(self, pos):
        return self.view.scene.items(pos)
    #endregion

    def ImportFromFile(self, data):
        self.truss=TrussModel()  
        for L in data:  
            L=L.strip()
            if L.find('#') == 0:
                pass 
            else:
                Cells=L.split(',')
                if len(Cells)<=1:
                    pass  
                elif Cells[0].lower().find('material')>=0:
                    sut=float(Cells[1].strip())
                    sy=float(Cells[2].strip())
                    E=float(Cells[3].strip())
                    self.truss.material=Material(uts=sut, ys=sy, modulus=E)
                elif Cells[0].lower().find('static')>=0:
                    sf=float(Cells[1].strip())
                    self.truss.material.staticFactor=sf
                elif Cells[0].lower().find('node')>=0:
                    name=Cells[1].strip()
                    x=float(Cells[2].strip())
                    y=float(Cells[3].strip())
                    self.truss.nodes.append(Node(name=name, position=Position(x=x,y=y)))
                elif Cells[0].lower().find('link') >= 0:
                    name=Cells[1].strip()
                    n1=Cells[2].strip()
                    n2=Cells[3].strip()
                    # $NEW$ Read new properties (default safely if using old file)
                    mat = Cells[4].strip() if len(Cells) > 4 else 'Steel'
                    w = float(Cells[5].strip()) if len(Cells) > 5 else 1.0
                    t = float(Cells[6].strip()) if len(Cells) > 6 else 0.25
                    self.truss.links.append(Link(name=name, node1=n1, node2=n2, material=mat, width=w, thickness=t))
        
        self.calcLinkVals()
        self.calcReactions() # $NEW$ Trigger physics
        self.displayReport()
        self.drawTruss()

    # ... (Keep hasNode, addNode, getNode, addLink exactly as they were) ...

    def calcLinkVals(self):
        for l in self.truss.links:
            n1 = self.getNode(l.node1_Name) if self.hasNode(l.node1_Name) else None
            n2 = self.getNode(l.node2_Name) if self.hasNode(l.node2_Name) else None
            
            if n1 is not None and n2 is not None:
                r=n2.position-n1.position
                l.length=r.mag()
                l.angleRad=r.getAngleRad()
                
                # $NEW$ Calculate Weight based on Material Density
                density = 0.283 if l.material.lower() == 'steel' else 0.098 # lb/in^3
                volume = l.length * l.width * l.thickness
                l.weight = volume * density

    def calcReactions(self):
        """
        $NEW$ Sums the moments about the Left node to find Right vertical load,
        then sums forces in Y to find Left vertical load.
        """
        left_n = self.getNode('Left')
        right_n = self.getNode('Right')
        if not left_n or not right_n: return

        span = right_n.position.x - left_n.position.x
        sum_M_left = 0
        total_weight = 0

        for l in self.truss.links:
            n1 = self.getNode(l.node1_Name)
            n2 = self.getNode(l.node2_Name)
            # Center of mass of the link
            cx = (n1.position.x + n2.position.x) / 2.0
            
            sum_M_left += l.weight * (cx - left_n.position.x)
            total_weight += l.weight

        right_n.reaction_y = sum_M_left / span if span != 0 else 0
        left_n.reaction_y = total_weight - right_n.reaction_y

    def setDisplayWidgets(self, args):
        self.view.setDisplayWidgets(args)

    def displayReport(self):
        self.view.displayReport(truss=self.truss)

    def drawTruss(self):
        self.view.buildScene(truss=self.truss)
#endregion