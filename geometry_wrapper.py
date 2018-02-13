# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeometryWrapper
                                 A QGIS plugin
 Converts geometry longitude from [-180,180] to [0,360]
                              -------------------
        begin                : 2017-03-16
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Jonah Sullivan
        email                : jonahsullivan79@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QMessageBox
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from geometry_wrapper_dialog import GeometryWrapperDialog
import os
import utils
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsMapLayerRegistry 


class GeometryWrapper:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeometryWrapper_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Geometry Wrapper')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'GeometryWrapper')
        self.toolbar.setObjectName(u'GeometryWrapper')
        
        # listen for browse button 
        self.dlg = GeometryWrapperDialog()
        self.dlg.inButton.clicked.connect(self.setInDataset) 

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GeometryWrapper', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        # self.dlg = GeometryWrapperDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/GeometryWrapper/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Geometry Wrapper'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Geometry Wrapper'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        
        # display file dialog to select input dataset
    def setInDataset(self):
        inName = QFileDialog.getOpenFileName(None, 
                                             'Select input dataset', 
                                             '', 
                                             "raster or vector (*.shp *.tif)",
                                             )
        if inName:
            self.inDataset = QFileInfo(inName).absoluteFilePath()
            self.dlg.inDataset.setText(QFileInfo(inName).absoluteFilePath())     

    def run(self):
        """Run method that performs all the real work"""
        # clear the indataset field
        self.inDataset = ''
        self.dlg.inDataset.clear()

        # show the dialog
        self.dlg.show()

        # set up an empty message box
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Geometry Wrapper")
        msg.setStandardButtons(QMessageBox.Ok)

        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # get raster or vector file type
            self.dataType = ''
            fileName = self.inDataset
            fileInfo = QFileInfo(self.inDataset)
            baseName = fileInfo.baseName()
            rlayer = QgsRasterLayer(fileName, baseName)
            vlayer = QgsVectorLayer(fileName, baseName, "ogr")
            if rlayer.isValid():
                self.dataType = 'raster'
                srs = rlayer.crs().authid()
                if srs != "EPSG:4326":
                    del rlayer
                    msg.setText("Input dataset must have EPSG:4326 projection")
                    msg.exec_()
                    self.run()
            elif vlayer.isValid():
                self.dataType = 'vector'
                srs = vlayer.crs().authid()
                if srs != "EPSG:4326":
                    del vlayer
                    msg.setText("Input dataset must have EPSG:4326 projection")
                    msg.exec_()
                    self.run()
            
            # check projection:
            
            # set output longitude range
            self.longitudeRange = 0
            if self.dlg.radioButton180.isChecked():
                self.longitudeRange = 180
            elif self.dlg.radioButton360.isChecked():
                self.longitudeRange = 360
                
            # send data for processing
            if self.dataType == 'vector':
                self.outFile = self.inDataset.split(os.extsep)[0] + "_" + str(self.longitudeRange) + ".shp"
                if os.path.exists(self.outFile):
                    msg.setText("Cannot overwrite existing file " + os.path.basename(self.outFile))
                    msg.exec_()
                    self.run()
                else:
                    utils.processVector(self.inDataset, self.longitudeRange, self.outFile)
                    fileInfo = QFileInfo(self.outFile)
                    baseName = fileInfo.baseName()
                    if self.dlg.addToToc.isChecked():
                        vlayer = QgsVectorLayer(self.outFile, unicode(baseName), "ogr")
                        if vlayer.isValid():
                            QgsMapLayerRegistry.instance().addMapLayers([vlayer])
            elif self.dataType == 'raster':
                self.outFile = self.inDataset.split(os.extsep)[0] + "_" + str(self.longitudeRange) + ".tif"
                if os.path.exists(self.outFile):
                    msg.setText("Cannot overwrite existing file " + os.path.basename(self.outFile))
                    msg.exec_()
                    self.run()
                else:
                    utils.processRaster(self.inDataset, self.longitudeRange, self.outFile)
                    fileInfo = QFileInfo(self.outFile)
                    baseName = fileInfo.baseName()
                    if self.dlg.addToToc.isChecked():
                        rlayer = QgsRasterLayer(self.outFile, unicode(baseName))
                        if rlayer.isValid():
                            QgsMapLayerRegistry.instance().addMapLayers([rlayer])
