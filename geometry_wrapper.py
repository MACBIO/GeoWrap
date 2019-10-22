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
from PyQt5.QtCore import QCoreApplication, QFileInfo
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QFileDialog, QMessageBox
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .geometry_wrapper_dialog import GeometryWrapperDialog
import os
from .utils import process_raster_file, process_vector_file
from .utils import process_raster_layer, process_vector_layer
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsProject


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

        # Declare instance attributes
        self.actions = []
        self.menu = u'&Geometry Wrapper'
        self.toolbar = self.iface.addToolBar(u'GeometryWrapper')
        self.toolbar.setObjectName(u'GeometryWrapper')

        # listen for browse button
        self.dlg = GeometryWrapperDialog()
        self.dlg.input_button.clicked.connect(self.set_in_dataset)

        # initialise other variables
        self.selected_tab = None
        self.input_dataset = None
        self.input_layer = None
        self.data_type = None
        self.longitude_range = None
        self.output_file = None
        self.output_layer = None

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
            text=u'Geometry Wrapper',
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                u'&Geometry Wrapper',
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

        # display file dialog to select input dataset

    def set_in_dataset(self):
        input_name = QFileDialog.getOpenFileName(None,
                                                 'Select input dataset',
                                                 '',
                                                 "raster or vector (*.shp *.tif)",
                                                 )
        if input_name:
            self.input_dataset = QFileInfo(input_name[0]).absoluteFilePath()
            self.dlg.input_dataset.setText(QFileInfo(input_name[0]).absoluteFilePath())

    def run(self):
        """Run method that performs all the real work"""
        # clear the input_dataset field
        self.dlg.input_dataset.clear()

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

            # check whether file or layer tab is selected
            if self.dlg.file_layer_tab_widget.currentIndex() == 0:
                self.selected_tab = "file"
            else:
                self.selected_tab = "layer"

            if self.selected_tab == "file":
                # get raster or vector file type
                self.data_type = ''
                file_name = self.input_dataset
                file_info = QFileInfo(self.input_dataset)
                base_name = file_info.baseName()
                raster_layer = QgsRasterLayer(file_name, base_name)
                vector_layer = QgsVectorLayer(file_name, base_name, "ogr")
                if raster_layer.isValid():
                    self.data_type = 'raster'
                    if raster_layer.crs().isGeograpic():
                        pass
                    else:
                        del raster_layer
                        msg.setText("Input dataset must have geographic coordinate system (such as WGS84)")
                        msg.exec_()
                        self.run()
                elif vector_layer.isValid():
                    self.data_type = 'vector'
                    if vector_layer.crs().isGeographic():
                        pass
                    else:
                        del vector_layer
                        msg.setText("Input dataset must have geographic coordinate system (such as WGS84)")
                        msg.exec_()
                        self.run()

                # check projection:

                # set output longitude range
                self.longitude_range = 0
                if self.dlg.radio_button180.isChecked():
                    self.longitude_range = 180
                elif self.dlg.radio_button360.isChecked():
                    self.longitude_range = 360

                # send data for processing
                if self.data_type == 'vector':
                    self.output_file = self.input_dataset.split(os.extsep)[0] + "_" + str(self.longitude_range) + ".shp"
                    if os.path.exists(self.output_file):
                        msg.setText("Cannot overwrite existing file " + os.path.basename(self.output_file))
                        msg.exec_()
                        self.run()
                    else:
                        process_vector_file(self.input_dataset, self.longitude_range, self.output_file)
                        file_info = QFileInfo(self.output_file)
                        base_name = file_info.baseName()
                        if self.dlg.add_to_toc.isChecked():
                            self.output_layer = QgsVectorLayer(self.output_file, base_name, "ogr")
                            if self.output_layer.isValid():
                                QgsProject.instance().addMapLayer(self.output_layer)
                elif self.data_type == 'raster':
                    self.output_file = self.input_dataset.split(os.extsep)[0] + "_" + str(self.longitude_range) + ".tif"
                    if os.path.exists(self.output_file):
                        msg.setText("Cannot overwrite existing file " + os.path.basename(self.output_file))
                        msg.exec_()
                        self.run()
                    else:
                        process_raster_file(self.input_dataset, self.longitude_range, self.output_file)
                        file_info = QFileInfo(self.output_file)
                        base_name = file_info.baseName()
                        if self.dlg.add_to_toc.isChecked():
                            self.output_layer = QgsRasterLayer(self.output_file, base_name)
                            if self.output_layer.isValid():
                                QgsProject.instance().addMapLayer(self.output_layer)

            elif self.selected_tab == "layer":
                self.input_layer = self.dlg.layer_combobox.currentLayer()
                if self.input_layer.type() == 0:
                    self.data_type = "vector"
                elif self.input_layer.type() == 1:
                    self.data_type = "raster"
                else:
                    msg.setText("Input dataset must be vector or raster")
                    msg.exec_()
                    self.run()
                if self.input_layer.crs().isGeographic():
                    pass
                else:
                    msg.setText("Input dataset must have geographic coordinate system (such as WGS84)")
                    msg.exec_()
                    self.run()

                if self.input_layer.isValid():
                    if self.data_type == "vector":
                        self.output_layer = process_vector_layer(self.input_layer, self.longitude_range)
                    else:
                        self.output_layer = process_raster_layer(self.input_layer, self.longitude_range)
                else:
                    msg.setText("Input layer is not valid for some reason")
                    msg.exec_()
                    self.run()

                QgsProject.instance().addMapLayer(self.output_layer)

