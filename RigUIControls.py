##############LEDLIGHTLines############################################
import sys
import weakref
import math
from PyQt4 import QtCore, QtGui
import numpy as np
import socket #for sending out UPD signals
import os
import FileControl
import xml.etree.ElementTree as xml

#######Project python imports################################################
from Utilities import *
from ControlItems import *

from Widgets import *
from RigStore import *

############################ MAIN RIG GRAPHICS VIEW #################################################################################

class RigGraphicsView(QtGui.QGraphicsView):

    def __init__(self, mainWindow, messageLogger, styleData, itemFactory):

        QtGui.QGraphicsView.__init__(self) 
        self.width = 500
        self.height = 500
        self.size = (0, 0, self.width, self.height)
        self.setAcceptDrops(True)

        self.messageLogger = messageLogger
        self.styleData = styleData
        self.itemFactory = itemFactory

        policy = QtCore.Qt.ScrollBarAlwaysOff
        self.setVerticalScrollBarPolicy(policy)
        self.setHorizontalScrollBarPolicy(policy)
        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)

        scene = QtGui.QGraphicsScene(self)
        scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        scene.setSceneRect(self.size[0],self.size[1],self.size[2],self.size[3])
        self.setScene(scene)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)

        self.scale(1,1)
        # self.setMinimumSize(500, 500)
        self.setWindowTitle(self.tr("Elastic Nodes"))
        self.inhibit_edit = False

        # View Settings
        self.backgroundImage = None

        self.markerCount = 1
        self.markerScale = 1.0
        self.markerActiveList = []   #Do not need to store this in XML since we can find the actual markers that have an

        #Add in Reflection Line
        self.reflectionLine = self.addReflectionLine()
        self.showReflectionLine = True

        #LARGE GROUP ATTRIBUTES
        self.markerList = []
        self.wireGroups = []
        self.superNodeGroups = []

        self.dragItem = None
        self.skinningItem = None
        self.isSelectableList = [] #list used to store selectable states while panning around 
        self.isMovableList = [] #list used to store selectable states while panning around       
        self.isSelectedList = []
        
        self.mainWindow = mainWindow

        #TESTING ADDING NEW ITEMS
        # el = ConstraintEllipse(80,80)
        # el.setPos(200,200)

        # rect = ConstraintRect(80,90)
        # rect.setPos(200,100)

        # line = ConstraintLine(50,25)
        # line.setPos(200,350)

        # el = SkinningEllipse()
        # el.setPos(200,200)

        # testSuperNode = SuperNodeGroup(QtCore.QPointF(50,25), "Arrow_4Point" ,self)
        # self.scene().addItem(testSuperNode)

        # self.scene().addItem(el)
        # self.scene().addItem(rect)
        # self.scene().addItem(line)

    def getBackgroundImage(self):
        return self.backgroundImage

    def setBackgroundImage(self, image):
        if image:   
            if os.path.exists(image):
                self.backgroundImage = image
            else: self.backgroundImage = None
        else: self.backgroundImage = None

    def getMarkerCount(self):
        return self.markerCount

    def setMarkerCount(self, markerCount):
        self.markerCount = markerCount

    def getMarkerScale(self):
        return self.markerScale

    def setMarkerScaleSlider(self, scale):
        """Function to cycle through markers and scale"""
        scene = self.scene()
        for item in scene.items():
            if type(item) == GuideMarker: #change the state of its show ID
                item.setScale(float(scale/100.0))
                item.update()
        self.markerScale = float(scale/100.0)

    def setMarkerScale(self,markerScale):
        self.markerScale = markerScale

    def getReflectionLine(self):
        return self.reflectionLine

    def setReflectionLine(self, reflectionLine):
        self.reflectionLine = reflectionLine

    def getMarkerList(self):
        return self.markerList

    def getWireGroups(self):
        return self.wireGroups

    def getSuperNodeGroups(self):
        return self.superNodeGroups

    def loadBackgroundImage(self):
        imagePath = QtGui.QFileDialog.getOpenFileName(caption = "Please choose front character face image ~ 500px x 500px", directory="./images" , filter = "*.png")
        if os.path.exists(imagePath):
            self.backgroundImage = imagePath 
            self.setupBackground() 


    def setupBackground(self, remap = True):
        """Function to set the validity of a file path, and if it is good then pass it to the Graphics View for drawing"""
        if self.backgroundImage:
            characterImage = QtGui.QPixmap(self.backgroundImage)
            self.width = characterImage.width()
            self.height = characterImage.height()
            self.size = [self.size[0],self.size[1], self.width,self.height]
            self.scene().setSceneRect(self.size[0],self.size[1],self.size[2],self.size[3])
            self.updateSceneRect(QtCore.QRectF(self.size[0],self.size[1],self.size[2],self.size[3]))
            if remap: self.reflectionLine.remap(self.width, self.height) # Adjust the Positing and height of the reflection line
            # self.setMinimumSize(self.width,self.height)
            self.scene().update()
            self.sizeHint()


    def addReflectionLine(self):
        scene = self.scene()
        refLine = ReflectionLine(self.width,self.height)
        scene.addItem(refLine)
        return refLine

    def setShowReflectionLine(self, state):
        """Function to show/hide the central reflection line"""
        self.reflectionLine.setVisible(state)
        self.reflectionLine.update()

    def add_guideMarker(self,pos):
        """Function to add a new node at the specified position!"""
        newMarker = GuideMarker()
        newMarker.setPos(self.mapToScene(pos))
        self.scene().addItem(newMarker)
        # print "Marker scene Pos : " + str(newMarker.scenePos())
        # print "Marker View pos : " + str(self.mapToScene(pos))
        return newMarker

    def get_ordered_nodes(self):
        nodes = [item for item in self.scene().items() if isinstance(item, Node)]
        nodes.sort(key=lambda n: n.index)
        return nodes

    def drawBackground(self, painter, rect):
        if self.backgroundImage != None:
            backImage = QtGui.QPixmap(self.backgroundImage)
            # backImage.scaled(500,500, QtCore.Qt.KeepAspectRatio)
            painter.drawPixmap(rect, backImage, rect)
            # print "This was drawn"
        sceneRect = self.sceneRect()
        # print "Back image is: " + str(self.backgroundImage)

    def reflectPos(self, pos):
        """Function to find the reflected position of a guide"""
        refLine = self.reflectionLine.pos().x()
        return QtCore.QPointF(refLine - (pos.x() - refLine), pos.y())

    def reflectGuides(self):
        scene = self.scene()
        """Function to find the list of selected Guide Markers and reflect them around the Reflection Line"""
        for item in scene.items():
            if type(item) == GuideMarker and item.isSelected() == True: #Find our selected GuideMarkers
                itemPos = item.pos() #Now build a marker at the reflected position
                newGuidePos = self.reflectPos(itemPos)
                newMarker = GuideMarker()
                newMarker.setIndex(item.getIndex())
                newMarker.setScale(self.markerScale)
                newMarker.setPos(newGuidePos.x(),newGuidePos.y())
                self.markerList.append(newMarker)
                scene.addItem(newMarker)

    def processMarkerActiveIndex(self):
        itemPresent = False
        for index, item in enumerate(self.markerActiveList):
            item.setActiveIndex(index)

    def processMarkerSelection(self, marker):
        itemPresent = False
        for item in self.markerActiveList:
            if marker == item: 
                itemPresent = True

        if itemPresent:
            if len(self.markerActiveList) > 1 :
                self.markerActiveList.remove(marker)
                marker.setActive(False) 
            elif len(self.markerActiveList) == 1: #The list only contains this master so clear the list to be empty and deactivate the marker
                self.markerActiveList = []
                marker.setActive(False)
        else: #the item is not present so we we just need to add it to the list
            self.markerActiveList.append(marker)
            marker.setActive(True)
        self.processMarkerActiveIndex()

    def processMarkerDelete(self, marker):
        itemPresent = False
        for item in self.markerActiveList:
            if marker == item: #the interacted item is in the list, so check if ctrl is pressed
                itemPresent = True

        if itemPresent: #the item is in the list so we need to remove it or, reset the list to empty
            if len(self.markerActiveList) > 1 :
                self.markerActiveList.remove(marker)
                marker.setActive(False)
            else: 
                self.markerActiveList = []
                marker.setActive(False)
        self.markerList.remove(marker) #Remove the marker from the main marker list


    def addWireGroup(self):
        "Function that looks at the makerSelection List and tried to build a Wire Rig"

        if len(self.markerActiveList) < 2:
            self.messageLogger.error("Not enough guide markers selected to create a wire group")
            return

        unique = True
        wireName, ok = QtGui.QInputDialog.getText(self, 'Wire Group Name', 'Enter a unique Wire Group Name:')
        while not self.checkUniqueWireGroup(wireName):
            wireName, ok = QtGui.QInputDialog.getText(
                    self,
                    'Wire Group Name',
                    'The name was not unique. Please Enter a unique Wire Group Name:'
                    )
        if ok:
            posList = []
            for m in self.markerActiveList: posList.append(m.pos())
            newWireGroup = WireGroup(self)
            newWireGroup.buildFromPositions(posList)
            newWireGroup.setScale(self.markerScale)
            print "wirename : " + str(wireName)
            newWireGroup.setName(str(wireName))
            self.wireGroups.append(newWireGroup)
            for m in self.markerActiveList:
                m.setActive(False)
                m.setSelected(False) #Deactivate all markers and deselect them
            self.markerActiveList = [] #Reset the Marker List

    def checkUniqueWireGroup(self, wireName):
        unique = True
        for wireGroup in self.wireGroups: 
            if wireName == wireGroup.getName(): unique = False
        return unique

    def showItem(self,state,objectType):
        """Function to hide and show markers"""
        scene = self.scene()
        for item in scene.items():
            if type(item) == objectType: #change the state of its show ID
                item.setVisible(state)
                item.update()
            if objectType == Node and type(item) == PinTie:
                item.setVisible(state)
                item.update()
            if objectType == ControlPin and type(item) == PinTie:
                item.setVisible(state)
                item.update()

    def selectFilter(self, state, objectType):
        """A function to control whether items can be selected or not"""
        scene = self.scene()
        for item in scene.items():
            if type(item) == objectType: #change the state of its show ID        
                item.setFlag(QtGui.QGraphicsItem.ItemIsMovable,state)
                item.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges,state)
                item.setFlag(QtGui.QGraphicsItem.ItemIsSelectable,state)
                if not state: item.setSelected(state)

    def panSelectableItems(self):
        """A function to turn off moveabliliy and selectablility on all objects for a pan"""
        self.isSelectableList = []
        self.isMovableList = []
        self.isSelectedList = []
        scene = self.scene()
        for item in scene.items():
            self.isSelectedList.append(item.isSelected())
            flags = item.flags()
            isSelectable = flags.__eq__(flags | QtGui.QGraphicsItem.ItemIsSelectable)
            self.isSelectableList.append(isSelectable) 
            isMovable = flags.__eq__(flags | QtGui.QGraphicsItem.ItemIsMovable)
            self.isMovableList.append(isMovable)
            item.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)  
            item.setFlag(QtGui.QGraphicsItem.ItemIsMovable, False) 

    def clear(self, isReflectionLine = True):
        self.scene().clear() # Clear the scene of all items
        self.setBackgroundImage(None)
        self.reflectionLine = None
        self.markerList = []
        self.markerActiveList = []
        self.wireGroups = []
        self.superNodeGroups = []
        if isReflectionLine: self.reflectionLine = self.addReflectionLine()

    def store(self, XMLFile):
        """Function to store all the contents of the Graphics View and write it out to a giant XML File - Work through all elements and Store"""
        GVRoot = xml.Element('faceRigGraphicsView')
        sceneItems = xml.SubElement(GVRoot,'sceneItems')
        for m in self.markerList:
            markerXML = m.store()
            # xml.tostring(markerXML)
            sceneItems.append(markerXML)
        GVXml = FileControl.XMLMan()
        GVXml.setTree(GVRoot)
        GVXml.setFile(XMLFile)
        GVXml.save()
        # print xml.tostring(GVRoot)

    def read(self, XMLFile):
        """Function to read in an entirely new Face Rig Graphics View"""
        scene = self.scene()
        GVXml = FileControl.XMLMan()
        GVXml.setLoad(XMLFile)
        GVMarkers = GVXml.findBranch("GuideMarker")
        for m in GVMarkers:
            newMarker = GuideMarker()
            newMarker.read(m)
            scene.addItem(newMarker)
            self.markerList.append(newMarker) #Add Marker to marker List
            # I Active then it should be added to the Active Marker List too!
            if newMarker.getActive(): self.markerActiveList.append(newMarker)
        self.markerActiveList.sort(key=lambda x: x.getActiveIndex())
        self.processMarkerActiveIndex()  #Update all active states    

    def keyPressEvent(self, event):
        scene = self.scene()
        key = event.key()
        if key == QtCore.Qt.Key_Alt:
            self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
            self.panSelectableItems()
        elif key == QtCore.Qt.Key_Plus:
            self.scaleView(1.2)
        elif key == QtCore.Qt.Key_Minus:
            self.scaleView(1 / 1.2)
        elif key == QtCore.Qt.Key_Delete:
            for item in scene.items():
                if type(item) == GuideMarker and item.isSelected() == True: #Delete out any GuideMarkers that are selection and need to be removed
                    self.processMarkerDelete(item)
                    scene.removeItem(item)
                    del item
            self.processMarkerActiveIndex()
        else:
            QtGui.QGraphicsView.keyPressEvent(self, event)

    # def sortSceneOrder(self):
    #     stackItems = []
    #     for item in self.scene().items(): stackItems.append(item)
    #     stackItems.sort(key=lambda x: x.zValue(), reverse=True)
    #     for item in self.scene().items(): self.scene().removeItem(item)
    #     for item in stackItems: self.scene().addItem(item)
    #     return stackItems

    def keyReleaseEvent(self, event):
        key = event.key()
        scene = self.scene()
        if key == QtCore.Qt.Key_Alt:
            self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
            for index, item in enumerate(scene.items()):
                item.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, self.isSelectableList[index])
                item.setFlag(QtGui.QGraphicsItem.ItemIsMovable, self.isMovableList[index])
                item.setSelected(self.isSelectedList[index])
        QtGui.QGraphicsView.keyReleaseEvent(self, event)

    def wheelEvent(self, event):
        self.scaleView(math.pow(2.0, -event.delta() / 240.0))

    def scaleView(self, scaleFactor):
        factor = self.matrix().scale(scaleFactor, scaleFactor).mapRect(QtCore.QRectF(0, 0, 1, 1)).width()
        if factor < 0.07 or factor > 100:
            return
        self.scale(scaleFactor, scaleFactor)

    def dragEnterEvent(self, event):
        """Function to overider dragEnterEvent to check that text is being used"""
        if (event.mimeData().hasFormat('text/plain')):
            data = QtCore.QString(event.mimeData().data('text/plain'))
            event.accept()
            print data
            if data == "GuideMarker":
                self.dragGuideMarker(event, data)
            elif data == "ConstraintLine" or data == "ConstraintRect" or data == "ConstraintEllipse":
                self.dragConstraintItem(event, data)
            elif data == "SuperNode_Arrow_4Point":
                self.dragSuperNode(event,"Arrow_4Point")
            elif data == "SuperNode_Arrow_sidePoint":
                self.dragSuperNode(event,"Arrow_sidePoint")
            elif data == "SuperNode_Arrow_upDownPoint":
                self.dragSuperNode(event,"Arrow_upDownPoint")
            elif data == "SkinningEllipse":
                self.dragSkinningEllipse(event)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Function to overider dragMoveEvent to check that text is being used"""
        if event.mimeData().hasFormat("text/plain"):
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            if self.dragItem:
                self.dragItem.setPos(self.mapToScene(event.pos()))
        else:
            event.ignore()

    def dropEvent(self, event): 
        """Function to overider dropEvent to check text has arrived and add it to the graphicsView as appropriate"""
        if (event.mimeData().hasFormat('text/plain')):
            self.processDrop(event)
        else:
            event.ignore() 

    def processDrop(self, event):
        scene = self.scene()
        dropNodes = []
        if type(self.dragItem) == ConstraintLine or type(self.dragItem) == ConstraintRect or type(self.dragItem) == ConstraintEllipse:
            possibleItems = self.items(event.pos())
            for item in possibleItems:
                if type(item) == Node or type(item) == SuperNode: dropNodes.append(item)
    
            if len(dropNodes) != 0 :
                dropNodes[0].goHome()
                self.dragItem.setPin(dropNodes[0].getPin()) # Add the constraint Item to the Pin
                self.dragItem.setPos(QtCore.QPointF(0,0))
                self.dragItem.setNode(dropNodes[0]) #Add the Node to the ConstraintItem
                if dropNodes[0].getPin().getConstraintItem():  # Check to see if the node already has a contraint Item, if it does then remove it so it can be replaced
                    scene.removeItem(dropNodes[0].getPin().getConstraintItem())
                    cItem = dropNodes[0].getPin().getConstraintItem()
                    del cItem
                dropNodes[0].getPin().setConstraintItem(self.dragItem) #Add the constraint Item to the pin
                self.dragItem.lock() #lock Movement so it cannot be dragged around
            else:
                scene.removeItem(self.dragItem) #We missed so delete the item
                self.dragItem = None

        if type(self.dragItem) == SkinningEllipse:
            possibleItems = self.items(event.pos())
            for item in possibleItems:
                if type(item) == SuperNode: dropNodes.append(item)

            if len(dropNodes) != 0 :
                dropNodes[0].goHome()
                self.dragItem.setPin(dropNodes[0].getPin()) # Add the constraint Item to the Pin
                self.dragItem.setPos(QtCore.QPointF(0,0))
                self.dragItem.setNode(dropNodes[0]) #Add the Node to the ConstraintItem
                dropNodes[0].setSkinningItem(self.dragItem)
                self.skinningItem = self.dragItem
                # dropNodes[0].getPin().setConstraintItem(self.dragItem) #Add the constraint Item to the pin
                self.dragItem.lock() #lock Movement so it cannot be dragged around
            else:
                scene.removeItem(self.dragItem) #We missed so delete the item
                self.dragItem = None

        if self.dragItem:
            self.dragItem.setAlpha(1.0)
            self.dragItem = None #reset the gv dragItem

        self.messageLogger.clear()

    def dragGuideMarker(self, event, data):
            event.acceptProposedAction()
            #Create a new QGraphicsItem and transfer the text across so we have the correct name
            data = QtCore.QString(event.mimeData().data("text/plain"))
            item = self.itemFactory.create(data)
            item.setIndex(self.markerCount)
            item.setPos(self.mapToScene(event.pos()))
            item.setScale(self.markerScale)
            item.setAlpha(0.5)
            self.markerList.append(item) #Add Item to the main Marker list
            self.scene().addItem(item)
            self.dragItem = item #set set the gv DragItem
            self.markerCount += 1

    def dragConstraintItem(self, event, data):
            event.acceptProposedAction()
            #Create a new QGraphicsItem and transfer the text across so we have the correct name
            data = QtCore.QString(event.mimeData().data("text/plain"))
            item = self.itemFactory.create(data)
            item.setPos(self.mapToScene(event.pos()))
            item.setAlpha(0.5)
            self.scene().addItem(item)
            self.dragItem = item #set set the gv DragItem

    def dragSuperNode(self, event, form):
            event.acceptProposedAction()
            #Create a new QGraphicsItem and transfer the text across so we have the correct name
            item = SuperNodeGroup(self.mapToScene(event.pos()), form, self)
            self.superNodeGroups.append(item)
            # item.setPos(self.mapToScene(event.pos()))
            # item.setAlpha(0.5)
            # self.scene().addItem(item)
            self.dragItem = item.getPin() #set set the gv DragItem


    def dragSkinningEllipse(self, event):
        event.acceptProposedAction()
        item = SkinningEllipse()
        item.setPos(self.mapToScene(event.pos()))
        item.setAlpha(0.5)
        self.dragItem = item #set set the gv DragItem
        self.scene().addItem(item)

    def mousePressEvent(self, mouseEvent):
        scene = self.scene()
        if mouseEvent.button() == QtCore.Qt.LeftButton:
            pass
            # for item in scene.items(QtCore.Qt.DescendingOrder): print str(type(item)) + " " + str(item.zValue())
            # possibleItems = self.items(mouseEvent.pos())
            # for item in possibleItems:
            #     print str(type(item)) + " " + str(item.zValue())
            # print "\n"
            # stacked = self.sortSceneOrder()
            # for item in stacked: print str(type(item)) + " " + str(item.zValue())

            # if mouseEvent.modifiers() & QtCore.Qt.ControlModifier:
            #     self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        return QtGui.QGraphicsView.mousePressEvent(self, mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        scene = self.scene()
        return QtGui.QGraphicsView.mouseMoveEvent(self, mouseEvent)


    def mouseDoubleClickEvent(self, mouseEvent):
        scene = self.scene()
        selGuides = []
        possibleItems = self.items(mouseEvent.pos())
        if mouseEvent.button() == QtCore.Qt.LeftButton:    #Left Double click on a Marker to activate or deactivate it
            for item in possibleItems:
                if type(item) == GuideMarker: selGuides.append(item)

        if len(selGuides) > 0 :
            self.processMarkerSelection(selGuides[0])
            self.processMarkerActiveIndex()
            return QtGui.QGraphicsView.mouseDoubleClickEvent(self, mouseEvent)

        if mouseEvent.button() == QtCore.Qt.MiddleButton:  #Send a Node back to its Pin with a Double Right button click
            for item in possibleItems:
               if type(item) == Node: 
                    item.goHome()
        return QtGui.QGraphicsView.mouseDoubleClickEvent(self, mouseEvent)

    def sortMenuItem(self, event):
        """Function to ensure that the correct RC menu appears where ever possible. Ensure that SkinningEllipse RC's do not appear over other items"""
        scene = self.scene()
        items = self.items(event.pos())
        noneSkinItems = False
        if len(items) != 0:
            for item in items: 
                if type(item) != SkinningEllipse: noneSkinItems = True
            if noneSkinItems: #We have other items present that are not skinningEllipses, so return the first one of them that we meet.
                for item in items: 
                    if type(item) != SkinningEllipse: return item
            else: return items[0] #If still false there are no other items under the event so return the skinning Ellipse

    def contextMenuEvent(self, event):
        # for item in items: print "Hit " + str(item)
        item = self.sortMenuItem(event) #Grab the appropriate Item
        if item:
            if type(item) == GuideMarker:
                self.guideMarkerContextMenu(event,item)
            elif type(item) == Node or type(item) == SuperNode:
                self.nodeContextMenu(event,item)
            elif type(item) == ControlPin:
                self.pinContextMenu(event,item)
            elif type(item) == ReflectionLine:
                self.reflectionLineContextMenu(event,item)
            # elif type(item) == SkinningEllipse:
            #     self.skinningEllipseContextMenu(event,item)
                # menu.addAction('ControlPin')

    def reflectionLineContextMenu(self,event,item):
        scene = self.scene()
        menu = QtGui.QMenu()
        menu.setStyleSheet(self.styleData)
        if item.getAdjustable():
            menu.addAction('Lock')
        else:
            menu.addAction('Unlock')
        action = menu.exec_(event.globalPos())
        if action:
            if action.text() == 'Lock': self.reflectionLine.setAdjustable(False)
            elif action.text() == 'Unlock': self.reflectionLine.setAdjustable(True)

    def guideMarkerContextMenu(self,event,item):
        scene = self.scene()
        menu = QtGui.QMenu()
        menu.setStyleSheet(self.styleData)
        if item.getActive():
            menu.addAction('Deactivate')
        else:
            menu.addAction('Activate')
        menu.addSeparator()   
        menu.addAction('Delete')
        menu.addAction('Hide')
        action = menu.exec_(event.globalPos())
        if action:
            if action.text() == 'Deactivate' or action.text() == 'Activate':
                item.setActive(not item.getActive())
            elif action.text() == 'Delete':
                self.processMarkerDelete(item)
                scene.removeItem(item)
                del item
            elif action.text() == 'Hide':
                item.setVisible(False)


    def nodeContextMenu(self,event,item):
        scene = self.scene()
        menu = QtGui.QMenu()
        menu.setStyleSheet(self.styleData)
        menu.addAction('Go Home')
        menu.addSeparator()
        if type(item) == Node: 
            menu.addAction('Reset Wire Group')
            menu.addSeparator()
        if item.getPin().getConstraintItem(): #Check the Node has a constraint item
            constrainMenu = QtGui.QMenu()
            constrainMenu.setStyleSheet(self.styleData)
            constrainMenu.setTitle("Constraint Area")
            constrainMenu.addAction('Show')
            constrainMenu.addAction('Ghost')
            constrainMenu.addAction('Hide')
            menu.addMenu(constrainMenu)
        menu.addSeparator()
        menu.addAction("Set Colour")
        isValidNodes, nodeSkinList = self.isNodesSelected()
        # print "ValidNodes " + str(isValidNodes)
        # print "Node List " + str(nodeSkinList)
        if type(item) == SuperNode and item.getSkinningItem() and isValidNodes:
            menu.addSeparator()
            menu.addAction('Skin Selected Nodes')

        action = menu.exec_(event.globalPos())
        if action:
            if action.text() == 'Go Home':
                item.goHome()
            elif action.text() == 'Reset Wire Group':
                item.resetWireGroup()
            elif action.text() == 'Show':
                item.getPin().getConstraintItem().setGhostArea(False)
                item.getPin().getConstraintItem().setVisible(True)
            elif action.text() == 'Ghost':
                item.getPin().getConstraintItem().setGhostArea(True)
                item.getPin().getConstraintItem().setVisible(True)   
            elif action.text() == 'Hide':
                item.getPin().getConstraintItem().setGhostArea(False)
                item.getPin().getConstraintItem().setVisible(False) 
            elif action.text() == 'Set Colour':
                newCol = QtGui.QColorDialog.getColor()
                if newCol.isValid():
                    if type(item) == Node: #If we are a node in a wire group then set all the node colours
                        if item.wireGroup:
                            for node in item.wireGroup.nodes: node.setColour(newCol)
                        else: item.setColour(newCol)
                    else: item.setColour(newCol)
            elif action.text() == 'Skin Selected Nodes':
                item.setSkinnedPins(nodeSkinList) #Grab the previously calculated valid Node List and Skin them


    def pinContextMenu(self,event,item):
        scene = self.scene()
        menu = QtGui.QMenu()
        menu.setStyleSheet(self.styleData)
        if item.isActive(): menu.addAction('Deactivate')
        else: menu.addAction('Activate')
        menu.addSeparator()
        if item.isLocked(): menu.addAction('Unlock')
        else: menu.addAction('Lock')

        action = menu.exec_(event.globalPos())
        if action:
            if action.text() == 'Activate':
                item.setActive(True)
                item.activate()
            elif action.text() == 'Deactivate':
                item.setActive(False)
                item.activate() 
            elif action.text() == 'Unlock':
                item.setLocked(False)    
            elif action.text() == 'Lock':
                item.setLocked(True)

    def isNodesSelected(self):
        selectedNodes = []
        circleSelectedNodes = []
        isNodes = False
        for item in self.scene().selectedItems():
            if type(item) == Node:
                if self.skinningItem: #check that not only is the node selected but it lies within the skinning circle
                    if self.skinningItem.contains(self.skinningItem.mapFromScene(int(item.getPin().scenePos().x()),int(item.getPin().scenePos().y()))):
                        selectedNodes.append(item)
                        isNodes = True
                        # print "Node Pin is in"
                else: 
                    selectedNodes.append(item)
                    isNodes = True
        return isNodes, selectedNodes

    def populateSkinningTable(self, superNode):
        self.mainWindow.skinTableWidget.setSuperNode(superNode)
        self.mainWindow.skinTableWidget.populate()

