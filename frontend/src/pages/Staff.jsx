import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { Plus, Users, Pencil, Trash, UserCircle, Phone } from "@phosphor-icons/react";

export default function Staff() {
  const [staffList, setStaffList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingStaff, setEditingStaff] = useState(null);
  const [typeFilter, setTypeFilter] = useState("all");

  const [formData, setFormData] = useState({
    name: "",
    staff_type: "Army",
    designation: "",
    contact_number: "",
    is_active: true
  });

  const fetchStaff = async () => {
    try {
      const response = await axios.get(`${API}/staff?active_only=false`);
      setStaffList(response.data);
    } catch (error) {
      console.error("Error fetching staff:", error);
      toast.error("Failed to load staff");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStaff();
  }, []);

  const filteredStaff = staffList.filter(s => {
    if (typeFilter === "all") return true;
    return s.staff_type === typeFilter;
  });

  const handleSubmit = async () => {
    if (!formData.name || !formData.staff_type) {
      toast.error("Please fill required fields");
      return;
    }

    try {
      if (editingStaff) {
        await axios.put(`${API}/staff/${editingStaff.id}`, formData);
        toast.success("Staff updated successfully!");
      } else {
        await axios.post(`${API}/staff`, formData);
        toast.success("Staff added successfully!");
      }
      setShowDialog(false);
      resetForm();
      fetchStaff();
    } catch (error) {
      console.error("Error saving staff:", error);
      toast.error("Failed to save staff");
    }
  };

  const handleDelete = async (staffId) => {
    if (!window.confirm("Are you sure you want to delete this staff member?")) return;

    try {
      await axios.delete(`${API}/staff/${staffId}`);
      toast.success("Staff deleted successfully!");
      fetchStaff();
    } catch (error) {
      console.error("Error deleting staff:", error);
      toast.error("Failed to delete staff");
    }
  };

  const openEditDialog = (staff) => {
    setEditingStaff(staff);
    setFormData({
      name: staff.name,
      staff_type: staff.staff_type,
      designation: staff.designation || "",
      contact_number: staff.contact_number || "",
      is_active: staff.is_active
    });
    setShowDialog(true);
  };

  const resetForm = () => {
    setEditingStaff(null);
    setFormData({
      name: "",
      staff_type: "Army",
      designation: "",
      contact_number: "",
      is_active: true
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="staff-loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="staff-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-800" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Staff
          </h1>
          <p className="text-slate-500 mt-1">Manage staff members</p>
        </div>
        <Button 
          onClick={() => { resetForm(); setShowDialog(true); }}
          className="earms-btn-primary flex items-center gap-2"
          data-testid="add-staff-btn"
        >
          <Plus size={20} />
          Add Staff
        </Button>
      </div>

      {/* Filter */}
      <Card className="earms-card">
        <CardContent className="p-4">
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-48" data-testid="type-filter">
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="Army">Army</SelectItem>
              <SelectItem value="Civilian">Civilian</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Staff Grid */}
      {filteredStaff.length === 0 ? (
        <Card className="earms-card">
          <CardContent className="py-12 text-center">
            <Users size={48} className="mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500">No staff members found</p>
            <Button 
              variant="outline" 
              className="mt-4"
              onClick={() => { resetForm(); setShowDialog(true); }}
            >
              Add First Staff Member
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredStaff.map((staff) => (
            <Card 
              key={staff.id} 
              className={`earms-card ${!staff.is_active ? 'opacity-60' : ''}`}
              data-testid={`staff-card-${staff.id}`}
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-3 rounded-full ${
                      staff.staff_type === "Army" ? "bg-emerald-100" : "bg-blue-100"
                    }`}>
                      <UserCircle 
                        size={28} 
                        weight="fill"
                        className={staff.staff_type === "Army" ? "text-emerald-600" : "text-blue-600"} 
                      />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-800">{staff.name}</h3>
                      <p className="text-sm text-slate-500">{staff.designation || "Staff"}</p>
                    </div>
                  </div>
                  <Badge className={staff.staff_type === "Army" ? "badge-success" : "badge-info"}>
                    {staff.staff_type}
                  </Badge>
                </div>

                {staff.contact_number && (
                  <div className="flex items-center gap-2 mt-4 text-sm text-slate-500">
                    <Phone size={16} />
                    {staff.contact_number}
                  </div>
                )}

                <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100">
                  <Badge variant="outline" className={staff.is_active ? "text-emerald-600" : "text-slate-400"}>
                    {staff.is_active ? "Active" : "Inactive"}
                  </Badge>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => openEditDialog(staff)}
                      data-testid={`edit-staff-${staff.id}`}
                    >
                      <Pencil size={16} />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-red-500 hover:text-red-600 hover:bg-red-50"
                      onClick={() => handleDelete(staff.id)}
                      data-testid={`delete-staff-${staff.id}`}
                    >
                      <Trash size={16} />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent data-testid="staff-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users size={24} className="text-blue-500" />
              {editingStaff ? "Edit Staff" : "Add New Staff"}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <Label>Name *</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Full name"
                className="earms-input mt-1"
                data-testid="input-staff-name"
              />
            </div>

            <div>
              <Label>Staff Type *</Label>
              <Select 
                value={formData.staff_type} 
                onValueChange={(v) => setFormData({...formData, staff_type: v})}
              >
                <SelectTrigger className="earms-input mt-1" data-testid="select-staff-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Army">Army</SelectItem>
                  <SelectItem value="Civilian">Civilian</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Designation</Label>
              <Input
                value={formData.designation}
                onChange={(e) => setFormData({...formData, designation: e.target.value})}
                placeholder="e.g., Receptionist, Caretaker"
                className="earms-input mt-1"
                data-testid="input-designation"
              />
            </div>

            <div>
              <Label>Contact Number</Label>
              <Input
                value={formData.contact_number}
                onChange={(e) => setFormData({...formData, contact_number: e.target.value})}
                placeholder="Phone number"
                className="earms-input mt-1"
                data-testid="input-contact"
              />
            </div>

            {editingStaff && (
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                <div>
                  <Label>Active Status</Label>
                  <p className="text-sm text-slate-500">Enable or disable this staff member</p>
                </div>
                <Switch
                  checked={formData.is_active}
                  onCheckedChange={(v) => setFormData({...formData, is_active: v})}
                  data-testid="switch-active"
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} className="earms-btn-primary" data-testid="save-staff-btn">
              {editingStaff ? "Update" : "Add"} Staff
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
