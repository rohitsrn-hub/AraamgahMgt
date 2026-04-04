import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Bed, Wrench, CheckCircle, XCircle } from "@phosphor-icons/react";

export default function Rooms() {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [showStatusDialog, setShowStatusDialog] = useState(false);
  const [newStatus, setNewStatus] = useState("");

  const fetchRooms = async () => {
    try {
      const response = await axios.get(`${API}/rooms`);
      setRooms(response.data);
    } catch (error) {
      console.error("Error fetching rooms:", error);
      toast.error("Failed to load rooms");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRooms();
  }, []);

  const filteredRooms = rooms.filter(room => {
    const matchesCategory = categoryFilter === "all" || room.category === categoryFilter;
    const matchesStatus = statusFilter === "all" || room.status === statusFilter;
    return matchesCategory && matchesStatus;
  });

  const handleStatusChange = async () => {
    if (!newStatus) return;

    try {
      await axios.put(`${API}/rooms/${selectedRoom.id}`, { status: newStatus });
      toast.success("Room status updated!");
      setShowStatusDialog(false);
      setSelectedRoom(null);
      fetchRooms();
    } catch (error) {
      console.error("Error updating room:", error);
      toast.error("Failed to update room status");
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "available": return <CheckCircle size={20} className="text-emerald-500" weight="fill" />;
      case "occupied": return <XCircle size={20} className="text-red-500" weight="fill" />;
      case "maintenance": return <Wrench size={20} className="text-amber-500" weight="fill" />;
      default: return null;
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case "available": return "available";
      case "occupied": return "occupied";
      case "maintenance": return "maintenance";
      default: return "";
    }
  };

  const catIRooms = filteredRooms.filter(r => r.category === "Cat I");
  const catIIRooms = filteredRooms.filter(r => r.category === "Cat II");

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="rooms-loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="rooms-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-800" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Rooms
          </h1>
          <p className="text-slate-500 mt-1">View and manage room status</p>
        </div>
      </div>

      {/* Filters */}
      <Card className="earms-card">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-40" data-testid="category-filter">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="Cat I">Cat I</SelectItem>
                <SelectItem value="Cat II">Cat II</SelectItem>
              </SelectContent>
            </Select>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40" data-testid="status-filter">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="available">Available</SelectItem>
                <SelectItem value="occupied">Occupied</SelectItem>
                <SelectItem value="maintenance">Maintenance</SelectItem>
              </SelectContent>
            </Select>

            {/* Legend */}
            <div className="flex items-center gap-4 ml-auto">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-emerald-100 border-2 border-emerald-300 rounded"></div>
                <span className="text-sm text-slate-600">Available</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-100 border-2 border-red-300 rounded"></div>
                <span className="text-sm text-slate-600">Occupied</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-amber-100 border-2 border-amber-300 rounded"></div>
                <span className="text-sm text-slate-600">Maintenance</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Cat I Rooms */}
      {catIRooms.length > 0 && (
        <Card className="earms-card" data-testid="cat-i-rooms-section">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              Cat I Rooms ({catIRooms.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {catIRooms.map((room) => (
                <div
                  key={room.id}
                  className={`room-card ${getStatusClass(room.status)}`}
                  onClick={() => {
                    setSelectedRoom(room);
                    setNewStatus(room.status);
                    setShowStatusDialog(true);
                  }}
                  data-testid={`room-card-${room.id}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-lg">{room.room_number}</span>
                    {getStatusIcon(room.status)}
                  </div>
                  <div className="text-xs text-slate-500">Floor {room.floor}</div>
                  <Badge 
                    variant="outline" 
                    className={`mt-2 text-xs ${
                      room.status === "available" ? "border-emerald-300 text-emerald-700" :
                      room.status === "occupied" ? "border-red-300 text-red-700" :
                      "border-amber-300 text-amber-700"
                    }`}
                  >
                    {room.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Cat II Rooms */}
      {catIIRooms.length > 0 && (
        <Card className="earms-card" data-testid="cat-ii-rooms-section">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
              Cat II Rooms ({catIIRooms.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {catIIRooms.map((room) => (
                <div
                  key={room.id}
                  className={`room-card ${getStatusClass(room.status)}`}
                  onClick={() => {
                    setSelectedRoom(room);
                    setNewStatus(room.status);
                    setShowStatusDialog(true);
                  }}
                  data-testid={`room-card-${room.id}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-lg">{room.room_number}</span>
                    {getStatusIcon(room.status)}
                  </div>
                  <div className="text-xs text-slate-500">Floor {room.floor}</div>
                  <Badge 
                    variant="outline" 
                    className={`mt-2 text-xs ${
                      room.status === "available" ? "border-emerald-300 text-emerald-700" :
                      room.status === "occupied" ? "border-red-300 text-red-700" :
                      "border-amber-300 text-amber-700"
                    }`}
                  >
                    {room.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {filteredRooms.length === 0 && (
        <Card className="earms-card">
          <CardContent className="py-12 text-center">
            <Bed size={48} className="mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500">No rooms found matching your filters</p>
          </CardContent>
        </Card>
      )}

      {/* Status Change Dialog */}
      <Dialog open={showStatusDialog} onOpenChange={setShowStatusDialog}>
        <DialogContent data-testid="room-status-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Bed size={24} className="text-blue-500" />
              Room {selectedRoom?.room_number}
            </DialogTitle>
          </DialogHeader>

          {selectedRoom && (
            <div className="space-y-4 py-4">
              <div className="p-4 bg-slate-50 rounded-xl">
                <p className="font-medium">{selectedRoom.category}</p>
                <p className="text-sm text-slate-500">Floor {selectedRoom.floor}</p>
                <p className="text-sm text-slate-500 mt-1">
                  Current Status: <span className="font-medium capitalize">{selectedRoom.status}</span>
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Change Status
                </label>
                <Select value={newStatus} onValueChange={setNewStatus}>
                  <SelectTrigger data-testid="select-new-status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="available">Available</SelectItem>
                    <SelectItem value="occupied">Occupied</SelectItem>
                    <SelectItem value="maintenance">Maintenance</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowStatusDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleStatusChange} 
              className="earms-btn-primary"
              data-testid="confirm-status-change"
            >
              Update Status
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
