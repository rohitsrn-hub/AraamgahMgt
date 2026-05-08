import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { generateToiletryReportPDF } from "@/utils/pdfUtils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import {
  Plus,
  Package,
  ArrowUp,
  ArrowDown,
  Warning,
  Pencil,
  Trash,
  ClipboardText,
  FilePdf,
  CalendarBlank,
} from "@phosphor-icons/react";
import { format, parseISO } from "date-fns";

export default function Toiletry() {
  const [items, setItems] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("inventory");
  
  // Dialog states
  const [showItemDialog, setShowItemDialog] = useState(false);
  const [showStockInDialog, setShowStockInDialog] = useState(false);
  const [showConsumptionDialog, setShowConsumptionDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);

  // Form states
  const [itemForm, setItemForm] = useState({
    name: "",
    quantity: 0,
    unit: "pcs",
    min_stock_level: 10
  });

  const [transactionForm, setTransactionForm] = useState({
    quantity: 0,
    notes: "",
    room_number: ""
  });

  // Report date range
  const [reportFromDate, setReportFromDate] = useState("");
  const [reportToDate, setReportToDate] = useState("");
  const [reportLoading, setReportLoading] = useState(false);

  const fetchData = async () => {
    try {
      const [itemsRes, transactionsRes] = await Promise.all([
        axios.get(`${API}/toiletry/items`),
        axios.get(`${API}/toiletry/transactions`)
      ]);
      setItems(itemsRes.data);
      setTransactions(transactionsRes.data);
    } catch (error) {
      console.error("Error fetching toiletry data:", error);
      toast.error("Failed to load toiletry data");
    } finally {
      setLoading(false);
    }
  };

  const handleFetchReport = async () => {
    setReportLoading(true);
    try {
      const params = new URLSearchParams();
      if (reportFromDate) params.append("from_date", reportFromDate);
      if (reportToDate) params.append("to_date", reportToDate + "T23:59:59");
      const res = await axios.get(`${API}/toiletry/transactions?${params}`);
      const result = generateToiletryReportPDF(res.data, reportFromDate, reportToDate);
      window.open(result.blobUrl, "_blank");
      toast.success(`PDF report generated — ${res.data.length} transaction(s)`);
    } catch {
      toast.error("Failed to generate report");
    } finally {
      setReportLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSaveItem = async () => {
    if (!itemForm.name) {
      toast.error("Please enter item name");
      return;
    }

    try {
      if (editingItem) {
        await axios.put(`${API}/toiletry/items/${editingItem.id}`, itemForm);
        toast.success("Item updated!");
      } else {
        await axios.post(`${API}/toiletry/items`, itemForm);
        toast.success("Item added!");
      }
      setShowItemDialog(false);
      resetItemForm();
      fetchData();
    } catch (error) {
      console.error("Error saving item:", error);
      toast.error("Failed to save item");
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (!window.confirm("Delete this item?")) return;

    try {
      await axios.delete(`${API}/toiletry/items/${itemId}`);
      toast.success("Item deleted!");
      fetchData();
    } catch (error) {
      console.error("Error deleting item:", error);
      toast.error("Failed to delete item");
    }
  };

  const handleStockIn = async () => {
    if (transactionForm.quantity <= 0) {
      toast.error("Enter valid quantity");
      return;
    }

    try {
      await axios.post(`${API}/toiletry/stock-in`, {
        item_id: selectedItem.id,
        quantity: transactionForm.quantity,
        notes: transactionForm.notes
      });
      toast.success("Stock added!");
      setShowStockInDialog(false);
      resetTransactionForm();
      fetchData();
    } catch (error) {
      console.error("Error adding stock:", error);
      toast.error("Failed to add stock");
    }
  };

  const handleConsumption = async () => {
    if (transactionForm.quantity <= 0) {
      toast.error("Enter valid quantity");
      return;
    }

    try {
      await axios.post(`${API}/toiletry/consumption`, {
        item_id: selectedItem.id,
        quantity: transactionForm.quantity,
        room_number: transactionForm.room_number,
        notes: transactionForm.notes
      });
      toast.success("Consumption recorded!");
      setShowConsumptionDialog(false);
      resetTransactionForm();
      fetchData();
    } catch (error) {
      console.error("Error recording consumption:", error);
      toast.error(error.response?.data?.detail || "Failed to record consumption");
    }
  };

  const resetItemForm = () => {
    setEditingItem(null);
    setItemForm({
      name: "",
      quantity: 0,
      unit: "pcs",
      min_stock_level: 10
    });
  };

  const resetTransactionForm = () => {
    setSelectedItem(null);
    setTransactionForm({
      quantity: 0,
      notes: "",
      room_number: ""
    });
  };

  const openEditDialog = (item) => {
    setEditingItem(item);
    setItemForm({
      name: item.name,
      quantity: item.quantity,
      unit: item.unit,
      min_stock_level: item.min_stock_level
    });
    setShowItemDialog(true);
  };

  const lowStockItems = items.filter(i => i.quantity <= i.min_stock_level);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="toiletry-loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="toiletry-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-800" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Toiletry Inventory
          </h1>
          <p className="text-slate-500 mt-1">Manage toiletry stock and consumption</p>
        </div>
        <Button 
          onClick={() => { resetItemForm(); setShowItemDialog(true); }}
          className="earms-btn-primary flex items-center gap-2"
          data-testid="add-item-btn"
        >
          <Plus size={20} />
          Add Item
        </Button>
      </div>

      {/* Low Stock Alert */}
      {lowStockItems.length > 0 && (
        <Card className="earms-card border-amber-200 bg-amber-50" data-testid="low-stock-alert">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Warning size={24} className="text-amber-600" weight="fill" />
              <div>
                <p className="font-medium text-amber-800">Low Stock Alert</p>
                <p className="text-sm text-amber-600">
                  {lowStockItems.length} item(s) below minimum stock level: {lowStockItems.map(i => i.name).join(", ")}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="inventory" data-testid="tab-inventory">
            <Package size={18} className="mr-2" />
            Inventory
          </TabsTrigger>
          <TabsTrigger value="transactions" data-testid="tab-transactions">
            <ClipboardText size={18} className="mr-2" />
            Transactions
          </TabsTrigger>
        </TabsList>

        {/* Inventory Tab */}
        <TabsContent value="inventory" className="mt-6">
          {items.length === 0 ? (
            <Card className="earms-card">
              <CardContent className="py-12 text-center">
                <Package size={48} className="mx-auto text-slate-300 mb-4" />
                <p className="text-slate-500">No items in inventory</p>
                <Button 
                  variant="outline" 
                  className="mt-4"
                  onClick={() => { resetItemForm(); setShowItemDialog(true); }}
                >
                  Add First Item
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {items.map((item) => (
                <Card 
                  key={item.id} 
                  className={`earms-card ${item.quantity <= item.min_stock_level ? 'border-amber-300 bg-amber-50' : ''}`}
                  data-testid={`item-card-${item.id}`}
                >
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold text-slate-800">{item.name}</h3>
                        <p className="text-sm text-slate-500">Min: {item.min_stock_level} {item.unit}</p>
                      </div>
                      {item.quantity <= item.min_stock_level && (
                        <Badge className="badge-warning">Low Stock</Badge>
                      )}
                    </div>

                    <div className="text-center py-4">
                      <div className={`text-4xl font-bold ${
                        item.quantity <= item.min_stock_level ? 'text-amber-600' : 'text-slate-800'
                      }`}>
                        {item.quantity}
                      </div>
                      <div className="text-sm text-slate-500">{item.unit}</div>
                    </div>

                    <div className="flex gap-2 mt-4">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-emerald-600 border-emerald-200 hover:bg-emerald-50"
                        onClick={() => { setSelectedItem(item); setShowStockInDialog(true); }}
                        data-testid={`stock-in-${item.id}`}
                      >
                        <ArrowUp size={16} className="mr-1" />
                        Stock In
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-blue-600 border-blue-200 hover:bg-blue-50"
                        onClick={() => { setSelectedItem(item); setShowConsumptionDialog(true); }}
                        data-testid={`consume-${item.id}`}
                      >
                        <ArrowDown size={16} className="mr-1" />
                        Use
                      </Button>
                    </div>

                    <div className="flex justify-end gap-2 mt-3 pt-3 border-t border-slate-100">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => openEditDialog(item)}
                        data-testid={`edit-item-${item.id}`}
                      >
                        <Pencil size={16} />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-red-500 hover:text-red-600 hover:bg-red-50"
                        onClick={() => handleDeleteItem(item.id)}
                        data-testid={`delete-item-${item.id}`}
                      >
                        <Trash size={16} />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Transactions Tab */}
        <TabsContent value="transactions" className="mt-6">
          {/* Date Range Report */}
          <Card className="earms-card mb-4">
            <CardContent className="p-4">
              <h4 className="font-semibold text-slate-700 flex items-center gap-2 mb-3">
                <FilePdf size={16} className="text-blue-600" /> Generate Report
              </h4>
              <div className="flex flex-wrap gap-3 items-end">
                <div>
                  <Label className="text-xs text-slate-600">From Date</Label>
                  <input type="date" value={reportFromDate} onChange={e => setReportFromDate(e.target.value)}
                    className="earms-input block mt-1 text-sm" />
                </div>
                <div>
                  <Label className="text-xs text-slate-600">To Date</Label>
                  <input type="date" value={reportToDate} onChange={e => setReportToDate(e.target.value)}
                    className="earms-input block mt-1 text-sm" />
                </div>
                <Button onClick={handleFetchReport} disabled={reportLoading}
                  className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2">
                  <FilePdf size={16} />
                  {reportLoading ? "Generating..." : "PDF Report"}
                </Button>
                {(reportFromDate || reportToDate) && (
                  <Button variant="outline" onClick={() => { setReportFromDate(""); setReportToDate(""); }}
                    className="text-slate-600 text-sm">
                    Clear
                  </Button>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-2">Leave dates blank to include all transactions</p>
            </CardContent>
          </Card>

          <Card className="earms-card">
            <CardContent className="p-0">
              {transactions.length === 0 ? (
                <div className="py-12 text-center">
                  <ClipboardText size={48} className="mx-auto text-slate-300 mb-4" />
                  <p className="text-slate-500">No transactions recorded</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="data-table" data-testid="transactions-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Item</th>
                        <th>Type</th>
                        <th>Quantity</th>
                        <th>Room</th>
                        <th>Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((t) => (
                        <tr key={t.id} data-testid={`transaction-row-${t.id}`}>
                          <td>{format(parseISO(t.created_at), "dd MMM yyyy HH:mm")}</td>
                          <td className="font-medium">{t.item_name}</td>
                          <td>
                            <Badge className={t.transaction_type === "stock_in" ? "badge-success" : "badge-info"}>
                              {t.transaction_type === "stock_in" ? (
                                <><ArrowUp size={14} className="mr-1" /> Stock In</>
                              ) : (
                                <><ArrowDown size={14} className="mr-1" /> Used</>
                              )}
                            </Badge>
                          </td>
                          <td>{t.quantity}</td>
                          <td>{t.room_number || "-"}</td>
                          <td className="text-slate-500">{t.notes || "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add/Edit Item Dialog */}
      <Dialog open={showItemDialog} onOpenChange={setShowItemDialog}>
        <DialogContent data-testid="item-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Package size={24} className="text-blue-500" />
              {editingItem ? "Edit Item" : "Add New Item"}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <Label>Item Name *</Label>
              <Input
                value={itemForm.name}
                onChange={(e) => setItemForm({...itemForm, name: e.target.value})}
                placeholder="e.g., Soap, Towel"
                className="earms-input mt-1"
                data-testid="input-item-name"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Initial Quantity</Label>
                <Input
                  type="number"
                  value={itemForm.quantity}
                  onChange={(e) => setItemForm({...itemForm, quantity: parseInt(e.target.value) || 0})}
                  className="earms-input mt-1"
                  data-testid="input-quantity"
                />
              </div>
              <div>
                <Label>Unit</Label>
                <Select value={itemForm.unit} onValueChange={(v) => setItemForm({...itemForm, unit: v})}>
                  <SelectTrigger className="earms-input mt-1" data-testid="select-unit">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pcs">Pieces</SelectItem>
                    <SelectItem value="sets">Sets</SelectItem>
                    <SelectItem value="bottles">Bottles</SelectItem>
                    <SelectItem value="rolls">Rolls</SelectItem>
                    <SelectItem value="packets">Packets</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label>Minimum Stock Level</Label>
              <Input
                type="number"
                value={itemForm.min_stock_level}
                onChange={(e) => setItemForm({...itemForm, min_stock_level: parseInt(e.target.value) || 0})}
                className="earms-input mt-1"
                data-testid="input-min-stock"
              />
              <p className="text-sm text-slate-500 mt-1">Alert when stock falls below this level</p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowItemDialog(false)}>Cancel</Button>
            <Button onClick={handleSaveItem} className="earms-btn-primary" data-testid="save-item-btn">
              {editingItem ? "Update" : "Add"} Item
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Stock In Dialog */}
      <Dialog open={showStockInDialog} onOpenChange={setShowStockInDialog}>
        <DialogContent data-testid="stock-in-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-emerald-600">
              <ArrowUp size={24} />
              Stock In - {selectedItem?.name}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="p-4 bg-emerald-50 rounded-xl text-center">
              <p className="text-sm text-slate-500">Current Stock</p>
              <p className="text-2xl font-bold text-emerald-700">
                {selectedItem?.quantity} {selectedItem?.unit}
              </p>
            </div>

            <div>
              <Label>Quantity to Add *</Label>
              <Input
                type="number"
                value={transactionForm.quantity}
                onChange={(e) => setTransactionForm({...transactionForm, quantity: parseInt(e.target.value) || 0})}
                className="earms-input mt-1"
                data-testid="input-stock-in-qty"
              />
            </div>

            <div>
              <Label>Notes</Label>
              <Textarea
                value={transactionForm.notes}
                onChange={(e) => setTransactionForm({...transactionForm, notes: e.target.value})}
                placeholder="e.g., Monthly purchase"
                className="mt-1"
                data-testid="input-stock-in-notes"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowStockInDialog(false)}>Cancel</Button>
            <Button onClick={handleStockIn} className="bg-emerald-500 hover:bg-emerald-600" data-testid="confirm-stock-in">
              Add Stock
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Consumption Dialog */}
      <Dialog open={showConsumptionDialog} onOpenChange={setShowConsumptionDialog}>
        <DialogContent data-testid="consumption-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-blue-600">
              <ArrowDown size={24} />
              Record Usage - {selectedItem?.name}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="p-4 bg-blue-50 rounded-xl text-center">
              <p className="text-sm text-slate-500">Current Stock</p>
              <p className="text-2xl font-bold text-blue-700">
                {selectedItem?.quantity} {selectedItem?.unit}
              </p>
            </div>

            <div>
              <Label>Quantity Used *</Label>
              <Input
                type="number"
                value={transactionForm.quantity}
                onChange={(e) => setTransactionForm({...transactionForm, quantity: parseInt(e.target.value) || 0})}
                className="earms-input mt-1"
                data-testid="input-consume-qty"
              />
            </div>

            <div>
              <Label>Room Number (Optional)</Label>
              <Input
                value={transactionForm.room_number}
                onChange={(e) => setTransactionForm({...transactionForm, room_number: e.target.value})}
                placeholder="e.g., C1-01"
                className="earms-input mt-1"
                data-testid="input-room-number"
              />
            </div>

            <div>
              <Label>Notes</Label>
              <Textarea
                value={transactionForm.notes}
                onChange={(e) => setTransactionForm({...transactionForm, notes: e.target.value})}
                placeholder="Additional notes..."
                className="mt-1"
                data-testid="input-consume-notes"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConsumptionDialog(false)}>Cancel</Button>
            <Button onClick={handleConsumption} className="bg-blue-500 hover:bg-blue-600" data-testid="confirm-consumption">
              Record Usage
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
