"""
defines the AreaPick class

http://www.paraview.org/Wiki/Selection_Implementation_in_VTK_and_ParaView_III
http://ruby-vtk.rubyforge.org/svn/trunk/VTK/Rendering/Testing/Cxx/TestAreaSelections.cxx
http://vtk.1045678.n5.nabble.com/picking-objects-from-a-subset-of-a-grid-td5143877.html
http://www.vtk.org/Wiki/VTK/Examples/Cxx/Picking/HighlightSelectedPoints
http://www.vtk.org/doc/nightly/html/classvtkExtractSelectedFrustum.html
http://www.vtk.org/doc/nightly/html/classvtkUnstructuredGridAlgorithm.html
http://www.vtk.org/doc/nightly/html/classvtkExtractCells.html
http://www.vtk.org/Wiki/VTK/Examples/Cxx/Picking/HighlightSelection
http://public.kitware.com/pipermail/vtkusers/2012-January/072046.html
http://vtk.1045678.n5.nabble.com/Getting-the-original-cell-id-s-from-vtkExtractUnstructuredGrid-td1239667.html
"""
from __future__ import print_function, division
import numpy as np
import vtk
#from vtk.util.numpy_support import vtk_to_numpy
#from pyNastran.gui.utils.vtk.vtk_utils import numpy_to_vtk_points
from pyNastran.utils.numpy_utils import integer_types


#vtkInteractorStyleRubberBandPick # sucks?
#class AreaPickStyle(vtk.vtkInteractorStyleDrawPolygon):  # not sure how to use this one...
class HighlightStyle(vtk.vtkInteractorStyleTrackballCamera):  # works
    """Highlights nodes & elements"""
    def __init__(self, parent=None, is_eids=True, is_nids=True, representation='wire',
                 name=None, callback=None):
        """creates the HighlightStyle instance"""
        self.AddObserver("LeftButtonPressEvent", self._left_button_press_event)
        #self.AddObserver("LeftButtonReleaseEvent", self._left_button_release_event)
        #self.AddObserver("RightButtonPressEvent", self.right_button_press_event)
        self.parent = parent
        self.highlight_button = self.parent.actions['highlight']
        #self.area_pick_button = self.parent.actions['area_pick']
        #self.picker_points = []
        #self.parent.area_picker.SetRenderer(self.parent.rend)
        self.is_eids = is_eids
        self.is_nids = is_nids
        self.representation = representation
        assert is_eids or is_nids, 'is_eids=%r is_nids=%r, must not both be False' % (is_eids, is_nids)
        self.callback = callback
        #self._pick_visible = False
        self.name = name
        assert name is not None

    def _left_button_press_event(self, obj, event):
        """
        gets the first point
        """
        self.OnLeftButtonDown()

        picker = self.parent.cell_picker
        pixel_x, pixel_y = self.parent.vtk_interactor.GetEventPosition()
        picker.Pick(pixel_x, pixel_y, 0, self.parent.rend)

        cell_id = picker.GetCellId()

        if cell_id < 0:
            return

        #icase = self.gui.icase_fringe
        #if icase is None:
            #return

        world_position = picker.GetPickPosition()

        grid = self.parent.gui.grid_selected
        cell_ids = [cell_id]
        point_ids = []
        if self.is_eids: # highlight_style = 'centroid
            actor = self._highlight_picker_cell(cell_id, grid)
        elif self.is_nids: # highlight_style = 'node'
            actor, point_ids = self._highlight_picker_node(cell_id, grid, world_position)
        else:
            raise RuntimeError('invalid highlight_style=%r' % self.highlight_style)


        #print('highlight_style  point_id=', point_id)
        self.actor = actor
        self.parent.vtk_interactor.Render()

        if self.callback is not None:
            eids, nids = map_cell_point_to_model(self.parent.gui, cell_ids, point_ids, name=None)
            self.callback(eids, nids, self.name)

        self.highlight_button.setChecked(False)

        # TODO: it would be nice if you could do a rotation without
        #       destroying the highlighted actor
        self.cleanup_observer = self.parent.setup_mouse_buttons(
            mode='default', left_button_down_cleanup=self.cleanup_callback)

    def cleanup_callback(self, obj, event):
        """this is the cleanup step to remove the highlighted actor"""
        self.parent.rend.RemoveActor(self.actor)
        #self.vtk_interactor.RemoveObservers('LeftButtonPressEvent')
        self.parent.vtk_interactor.RemoveObserver(self.cleanup_observer)
        cleanup_observer = None

    def _highlight_picker_node(self, cell_id, grid, node_xyz):
        """won't handle multiple cell_ids/node_xyz"""
        cell = grid.GetCell(cell_id)
        nnodes = cell.GetNumberOfPoints()
        points = cell.GetPoints()

        point0 = points.GetPoint(0)
        dist_min = vtk.vtkMath.Distance2BetweenPoints(point0, node_xyz)

        imin = 0
        #point_min = point0
        for ipoint in range(1, nnodes):
            #point = array(points.GetPoint(ipoint), dtype='float32')
            #dist = norm(point - node_xyz)
            point = points.GetPoint(ipoint)
            dist = vtk.vtkMath.Distance2BetweenPoints(point, node_xyz)
            if dist < dist_min:
                dist_min = dist
                imin = ipoint
                #point_min = point
        point_id = cell.GetPointId(imin)

        ids = vtk.vtkIdTypeArray()
        ids.SetNumberOfComponents(1)
        ids.InsertNextValue(point_id)

        selection_node = vtk.vtkSelectionNode()
        #selection_node.SetContainingCellsOn()
        #selection_node.Initialize()
        selection_node.SetFieldType(vtk.vtkSelectionNode.POINT)
        selection_node.SetContentType(vtk.vtkSelectionNode.INDICES)
        selection_node.SetSelectionList(ids)
        actor = self._highlight_picker_by_selection_node(
            grid, selection_node, representation='points')
        return actor, [point_id]

    def _highlight_picker_cell(self, cell_ids, grid):
        """won't handle multiple cell_ids/node_xyz"""
        if isinstance(cell_ids, integer_types):
            cell_ids = [cell_ids]
        ids = vtk.vtkIdTypeArray()
        ids.SetNumberOfComponents(1)
        for cell_id in cell_ids:
            ids.InsertNextValue(cell_id)

        selection_node = vtk.vtkSelectionNode()
        selection_node.SetFieldType(vtk.vtkSelectionNode.CELL)
        selection_node.SetContentType(vtk.vtkSelectionNode.INDICES)
        selection_node.SetSelectionList(ids)
        actor = self._highlight_picker_by_selection_node(
            grid, selection_node, representation='surface')
        return actor

    def _highlight_picker_by_selection_node(self, grid, selection_node,
                                            representation='surface'):
        """
        helper method for:
            - _highlight_picker_cell
            - _highlight_picker_node
        """
        selection = vtk.vtkSelection()
        selection.AddNode(selection_node)

        extract_selection = vtk.vtkExtractSelection()
        extract_selection.SetInputData(0, grid)
        extract_selection.SetInputData(1, selection)
        extract_selection.Update()

        ugrid = extract_selection.GetOutput()
        actor = self.parent.create_highlighted_actor(ugrid, representation=representation)
        return actor

def map_cell_point_to_model(gui, cell_ids, point_ids, name=None):
    eids = []
    nids = []
    if cell_ids:
        cell_array = np.asarray(cell_ids, dtype='int32')
        eids = gui.element_ids[cell_array]

    if point_ids:
        point_array = np.asarray(point_ids, dtype='int32')
        nids = gui.node_ids[point_array]
    return eids, nids