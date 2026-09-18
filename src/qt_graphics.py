from PySide6 import QtCore, QtWidgets, QtGui


class GraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


    def wheelEvent(self, event) -> None:
        zoom_in_factor = 1.25
        zoom_out_factor = 0.8

        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def panEvent(self, event) -> None:
        if event.buttons() == QtCore.Qt.MouseButton.MiddleButton:
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        else:
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)

class GraphicsImage(QtWidgets.QGraphicsPixmapItem):
    def __init__(self):
        super().__init__()
        self.setTransformationMode(QtCore.Qt.TransformationMode.SmoothTransformation)
        self.setFlags(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtCore.Qt.CursorShape.OpenHandCursor)
        self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.LeftButton)
        self.setZValue(1)
        self.setOpacity(1.0)
        self.setVisible(True)
        self.setToolTip("Orthographic Slice")