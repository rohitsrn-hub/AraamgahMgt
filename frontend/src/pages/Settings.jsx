import { useState } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { 
  Gear, 
  CurrencyInr, 
  Buildings,
  FloppyDisk,
  Info,
  Percent,
  Trash,
  Plus,
  User,
  Star
} from "@phosphor-icons/react";

const DEFAULT_COLORS = [
  "Red", "Green", "Brown", "Orange", "Yellow", 
  "Violet", "Black", "Blue", "White", "Light Blue"
];

export default function Settings({ settings, onUpdate }) {
  const [formData, setFormData] = useState({
    cat_i_rate: settings?.cat_i_rate || 500,
    cat_ii_rate: settings?.cat_ii_rate || 400,
    def_civ_cat_i_rate: settings?.def_civ_cat_i_rate || 600,
    def_civ_cat_ii_rate: settings?.def_civ_cat_ii_rate || 600,
    cat_i_room_rent: settings?.cat_i_room_rent || 470,
    cat_i_license_fee: settings?.cat_i_license_fee || 30,
    cat_ii_room_rent: settings?.cat_ii_room_rent || 385,
    cat_ii_license_fee: settings?.cat_ii_license_fee || 15,
    non_org_room_rent: settings?.non_org_room_rent || settings?.def_civ_room_rent || 570,
    non_org_license_fee: settings?.non_org_license_fee || settings?.def_civ_license_fee || 30,
    cat_i_rooms_count: settings?.cat_i_rooms_count || 6,
    cat_ii_rooms_count: settings?.cat_ii_rooms_count || 9,
    default_advance_amount: settings?.default_advance_amount || 400,
    colors: settings?.colors || [...DEFAULT_COLORS],
    cancellation_policy: settings?.cancellation_policy || [
      { days_before: 7, charge_percent: 0 },
      { days_before: 3, charge_percent: 25 },
      { days_before: 1, charge_percent: 50 },
      { days_before: 0, charge_percent: 100 }
    ]
  });
  const [saving, setSaving] = useState(false);
  const [newColor, setNewColor] = useState("");
  
  // P4: Room Categories Management
  const [categories, setCategories] = useState(
    settings?.room_categories || [
      { id: "cat-i", name: "Cat I", rate: 500, def_civ_rate: 600, room_count: 6, prefix: "C1", capacity: 2 },
      { id: "cat-ii", name: "Cat II", rate: 400, def_civ_rate: 600, room_count: 9, prefix: "C2", capacity: 2 }
    ]
  );

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/settings`, formData);
      toast.success("Settings saved successfully!");
      onUpdate();
    } catch (error) {
      console.error("Error saving settings:", error);
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const updateCancellationSlab = (index, field, value) => {
    const newPolicy = [...formData.cancellation_policy];
    newPolicy[index] = { ...newPolicy[index], [field]: parseFloat(value) || 0 };
    setFormData({ ...formData, cancellation_policy: newPolicy });
  };

  const addCancellationSlab = () => {
    setFormData({ ...formData, cancellation_policy: [...formData.cancellation_policy, { hours_before: 0, charge_percent: 0 }] });
  };

  const removeCancellationSlab = (index) => {
    if (formData.cancellation_policy.length <= 1) { toast.error("At least one slab is required"); return; }
    setFormData({ ...formData, cancellation_policy: formData.cancellation_policy.filter((_, i) => i !== index) });
  };

  const addColor = () => {
    const trimmed = newColor.trim();
    if (!trimmed) return;
    if (formData.colors.includes(trimmed)) { toast.error("Color already exists"); return; }
    setFormData({ ...formData, colors: [...formData.colors, trimmed] });
    setNewColor("");
    toast.success(`Color "${trimmed}" added. Click "Save Settings" below to persist!`, { duration: 5000 });
  };

  const removeColor = (color) => {
    setFormData({ ...formData, colors: formData.colors.filter(c => c !== color) });
    toast.info(`Color "${color}" removed. Click "Save Settings" to persist!`, { duration: 5000 });
  };

  const resetColors = () => {
    setFormData({ ...formData, colors: [...DEFAULT_COLORS] });
  };

  // P4: Category Management Functions
  const addCategory = () => {
    const newId = `cat-${Date.now()}`;
    setCategories([
      ...categories,
      { id: newId, name: "", rate: 0, def_civ_rate: 0, room_count: 0, prefix: "", capacity: 2 }
    ]);
  };

  const updateCategory = (index, field, value) => {
    const updated = [...categories];
    updated[index] = { ...updated[index], [field]: value };
    setCategories(updated);
  };

  const removeCategory = (index) => {
    if (categories.length <= 1) {
      toast.error("At least one category is required");
      return;
    }
    setCategories(categories.filter((_, i) => i !== index));
  };

  const saveCategories = async () => {
    // Validate categories
    for (const cat of categories) {
      if (!cat.name || !cat.prefix) {
        toast.error("All categories must have a name and prefix");
        return;
      }
      if (cat.rate <= 0 || cat.def_civ_rate <= 0) {
        toast.error("Rates must be greater than 0");
        return;
      }
      if (!cat.capacity || cat.capacity <= 0) {
        toast.error("Room capacity must be greater than 0");
        return;
      }
    }

    setSaving(true);
    try {
      await axios.put(`${API}/settings/categories`, categories);
      toast.success("Room categories updated successfully!");
      onUpdate();
    } catch (error) {
      console.error("Error saving categories:", error);
      toast.error("Failed to save categories");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="settings-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-800" style={{ fontFamily: 'Outfit, sans-serif' }}>
          Settings
        </h1>
        <p className="text-slate-500 mt-1">Configure SARAI system settings</p>
      </div>

      {/* P3: System Actions */}
      <div className="grid grid-cols-1 gap-4">
        {/* Migration Mode */}
        <Card className="earms-card border-2 border-amber-300">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <Info size={20} className="text-amber-600" weight="fill" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800">Migration Mode</h3>
                <p className="text-xs text-slate-500">Allow past-dated entries</p>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-700">
                {localStorage.getItem("migration_mode") === "true" ? "Enabled" : "Disabled"}
              </span>
              <Button
                onClick={() => {
                  const currentMode = localStorage.getItem("migration_mode") === "true";
                  localStorage.setItem("migration_mode", (!currentMode).toString());
                  toast.success(`Migration mode ${!currentMode ? "enabled" : "disabled"}`);
                  window.location.reload();
                }}
                variant={localStorage.getItem("migration_mode") === "true" ? "destructive" : "default"}
                size="sm"
              >
                {localStorage.getItem("migration_mode") === "true" ? "Disable" : "Enable"}
              </Button>
            </div>
            {localStorage.getItem("migration_mode") === "true" && (
              <p className="text-xs text-amber-700 mt-2 bg-amber-50 p-2 rounded">
                ⚠️ You can now create bookings and check-ins with past dates for data migration.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* P4: Room Categories Configuration */}
      <Card className="earms-card" data-testid="room-categories-section">
        <CardContent className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Buildings size={20} className="text-blue-600" weight="duotone" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-800">Room Categories</h2>
                <p className="text-sm text-slate-500">Configure room types, rates, and capacities</p>
              </div>
            </div>
            <Button type="button" onClick={addCategory} variant="outline" size="sm">
              <Plus size={16} className="mr-1" /> Add Category
            </Button>
          </div>

          <div className="space-y-3">
            {categories.map((cat, idx) => (
              <div key={cat.id} className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <div className="flex justify-between items-start mb-3">
                  <h3 className="font-semibold text-slate-700">Category {idx + 1}</h3>
                  {categories.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeCategory(idx)}
                      className="text-red-500 hover:text-red-700 h-8 w-8 p-0"
                    >
                      <Trash size={16} />
                    </Button>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs">Category Name *</Label>
                    <Input
                      value={cat.name}
                      onChange={(e) => updateCategory(idx, "name", e.target.value)}
                      onFocus={(e) => e.target.select()}
                      placeholder="e.g., Cat I, VIP Suite"
                      className="earms-input mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Prefix (for room numbers) *</Label>
                    <Input
                      value={cat.prefix}
                      onChange={(e) => updateCategory(idx, "prefix", e.target.value.toUpperCase())}
                      onFocus={(e) => e.target.select()}
                      placeholder="e.g., C1, VIP"
                      className="earms-input mt-1"
                      maxLength={3}
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Standard Rate (₹/night) *</Label>
                    <Input
                      type="number"
                      min="0"
                      value={cat.rate}
                      onChange={(e) => updateCategory(idx, "rate", parseFloat(e.target.value) || 0)}
                      onFocus={(e) => e.target.select()}
                      className="earms-input mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Non-Org Rate (₹/night) *</Label>
                    <Input
                      type="number"
                      min="0"
                      value={cat.def_civ_rate}
                      onChange={(e) => updateCategory(idx, "def_civ_rate", parseFloat(e.target.value) || 0)}
                      onFocus={(e) => e.target.select()}
                      className="earms-input mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Room Capacity (persons) *</Label>
                    <Input
                      type="number"
                      min="1"
                      value={cat.capacity || 2}
                      onChange={(e) => updateCategory(idx, "capacity", parseInt(e.target.value) || 2)}
                      onFocus={(e) => e.target.select()}
                      className="earms-input mt-1"
                      placeholder="e.g., 2"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Number of Rooms *</Label>
                    <Input
                      type="number"
                      min="0"
                      value={cat.room_count}
                      onChange={(e) => updateCategory(idx, "room_count", parseInt(e.target.value) || 0)}
                      onFocus={(e) => e.target.select()}
                      className="earms-input mt-1"
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      {cat.room_count > 0 && cat.prefix && `Will create rooms: ${cat.prefix}-01 to ${cat.prefix}-${String(cat.room_count).padStart(2, '0')}`}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={() => setCategories(settings?.room_categories || categories)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={saveCategories}
              disabled={saving}
              className="bg-blue-500 hover:bg-blue-600"
            >
              {saving ? "Saving..." : "Save Categories"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Room Rates Summary (Read-Only) */}
      <Card className="earms-card" data-testid="room-rates-section">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CurrencyInr size={24} className="text-emerald-500" weight="duotone" />
            Room Rates Summary
          </CardTitle>
          <p className="text-sm text-slate-500">Current room category rates (edit in Room Categories section above)</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {categories.map((cat, idx) => (
              <div key={cat.id} className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-slate-800 text-lg">{cat.name}</h3>
                    <p className="text-xs text-slate-500">Prefix: {cat.prefix} • {cat.room_count} rooms • Capacity: {cat.capacity} person{cat.capacity > 1 ? 's' : ''}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-blue-600 font-medium mb-1">Standard Rate</p>
                    <p className="text-2xl font-bold text-blue-700">₹{cat.rate}</p>
                    <p className="text-xs text-blue-600">per night</p>
                  </div>
                  <div className="p-3 bg-orange-50 rounded-lg">
                    <p className="text-xs text-orange-600 font-medium mb-1">Non-Org Rate</p>
                    <p className="text-2xl font-bold text-orange-700">₹{cat.def_civ_rate}</p>
                    <p className="text-xs text-orange-600">per night</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {categories.length === 0 && (
            <div className="text-center py-8 text-slate-400">
              <p>No room categories configured yet.</p>
              <p className="text-sm mt-2">Add categories in the Room Categories section above.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* License Fee Breakdown (for Monthly Report) */}
      <Card className="earms-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Percent size={24} className="text-blue-500" weight="duotone" />
            License Fee Breakdown
          </CardTitle>
          <p className="text-sm text-slate-500">For monthly financial report to calculate license fee payable to maintaining agency</p>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-blue-50 rounded-xl border border-blue-200 mb-4">
            <p className="text-xs text-blue-700">Total rate = Room Rent + License Fee. These are used in the monthly financial report to calculate the license fee payable to the maintaining agency.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              { label: "Org (Cat I)", rentKey: "cat_i_room_rent", feeKey: "cat_i_license_fee", bgClass: "bg-blue-50 border-blue-200", textClass: "text-blue-800", totalClass: "text-blue-700" },
              { label: "Org (Cat II)", rentKey: "cat_ii_room_rent", feeKey: "cat_ii_license_fee", bgClass: "bg-purple-50 border-purple-200", textClass: "text-purple-800", totalClass: "text-purple-700" },
              { label: "Non-Org", rentKey: "non_org_room_rent", feeKey: "non_org_license_fee", bgClass: "bg-orange-50 border-orange-200", textClass: "text-orange-800", totalClass: "text-orange-700" }
            ].map(({ label, rentKey, feeKey, bgClass, textClass, totalClass }) => (
              <div key={rentKey} className={`p-4 rounded-xl border ${bgClass}`}>
                <h4 className={`font-semibold mb-3 ${textClass}`}>{label}</h4>
                <div className="space-y-2">
                  <div>
                    <Label className="text-xs text-slate-500">Room Rent (₹)</Label>
                    <Input type="number" value={formData[rentKey]} onChange={(e) => setFormData({...formData, [rentKey]: parseFloat(e.target.value) || 0})} onFocus={(e) => e.target.select()} className="earms-input mt-1" data-testid={`input-${rentKey}`} />
                  </div>
                  <div>
                    <Label className="text-xs text-slate-500">License Fee (₹)</Label>
                    <Input type="number" value={formData[feeKey]} onChange={(e) => setFormData({...formData, [feeKey]: parseFloat(e.target.value) || 0})} onFocus={(e) => e.target.select()} className="earms-input mt-1" data-testid={`input-${feeKey}`} />
                  </div>
                  <div className={`text-xs font-semibold mt-2 p-2 bg-white rounded ${totalClass}`}>
                    Total = ₹{(formData[rentKey] || 0) + (formData[feeKey] || 0)}/night
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Colors Management */}
      <Card className="earms-card" data-testid="colors-section">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Star size={24} className="text-purple-500" weight="duotone" />
            Color Categories
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500 mb-4">
            Configure the color categories for Organization guests. These are used for classification and grouping in reports.
          </p>
          <div className="flex flex-wrap gap-2 mb-4">
            {formData.colors.map((color) => (
              <div
                key={color}
                className="flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium border bg-purple-100 border-purple-300 text-purple-800"
                data-testid={`color-chip-${color}`}
              >
                {color}
                <button
                  onClick={() => removeColor(color)}
                  className="ml-1 text-purple-400 hover:text-red-500 transition-colors"
                  data-testid={`remove-color-${color}`}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
          <div className="flex gap-2 mb-3">
            <Input
              value={newColor}
              onChange={(e) => setNewColor(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") addColor(); }}
              placeholder="Add new color..."
              className="earms-input"
              data-testid="input-new-color"
            />
            <Button onClick={addColor} variant="outline" data-testid="add-color-btn">
              <Plus size={18} className="mr-1" /> Add
            </Button>
          </div>
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              onClick={resetColors}
              className="text-sm text-slate-500 border-dashed"
              data-testid="reset-colors-btn"
            >
              Reset to Default (10 colors)
            </Button>
          </div>
          <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
            <p className="text-sm text-purple-800 font-medium flex items-center gap-2">
              <Info size={16} weight="fill" />
              Remember to click "Save Settings" button at the bottom of the page to persist changes!
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Default Advance Amount */}
      <Card className="earms-card" data-testid="advance-amount-section">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CurrencyInr size={24} className="text-amber-500" weight="duotone" />
            Booking Advance Amount
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="max-w-md">
            <Label className="text-slate-600 mb-2 block">Default Advance Payment Amount</Label>
            <div className="flex items-center gap-2">
              <span className="text-2xl text-amber-600">₹</span>
              <Input
                type="number"
                value={formData.default_advance_amount}
                onChange={(e) => setFormData({...formData, default_advance_amount: parseFloat(e.target.value) || 0})}
                onFocus={(e) => e.target.select()}
                className="earms-input text-xl font-bold"
                data-testid="input-default-advance"
              />
            </div>
            <p className="text-sm text-slate-500 mt-2">
              This amount will be pre-filled in the booking form as the default advance payment.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Cancellation Policy */}
      <Card className="earms-card" data-testid="cancellation-policy-section">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Percent size={24} className="text-red-500" weight="duotone" />
            Cancellation Policy (Graded Scale)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 bg-amber-50 rounded-xl border border-amber-200">
              <p className="text-sm text-amber-800">
                <strong>📋 How it works:</strong> Define cancellation charges based on <strong>hours</strong> before check-in time (13:00).
              </p>
              <p className="text-xs text-amber-700 mt-2">
                <strong>Current Policy:</strong><br/>
                • <strong>&gt;96 hours (4+ days):</strong> 100% refund<br/>
                • <strong>48-96 hours (2-4 days):</strong> 50% refund<br/>
                • <strong>&lt;48 hours (&lt;2 days):</strong> 0% refund (full charge)
              </p>
            </div>
            <div className="space-y-3">
              <div className="grid grid-cols-12 gap-4 text-sm font-medium text-slate-600 px-2">
                <div className="col-span-5">Hours Before Check-in</div>
                <div className="col-span-5">Cancellation Charge (%)</div>
                <div className="col-span-2"></div>
              </div>
              {formData.cancellation_policy
                .sort((a, b) => b.hours_before - a.hours_before)
                .map((slab, index) => (
                  <div key={index} className="grid grid-cols-12 gap-4 items-center p-3 bg-slate-50 rounded-xl">
                    <div className="col-span-5">
                      <div className="flex items-center gap-2">
                        <Input
                          type="number" min="0"
                          value={slab.hours_before}
                          onChange={(e) => updateCancellationSlab(index, 'hours_before', e.target.value)}
                          onFocus={(e) => e.target.select()}
                          className="earms-input"
                          data-testid={`input-hours-${index}`}
                        />
                        <span className="text-sm text-slate-500 whitespace-nowrap">hours or more</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1 ml-1">
                        {slab.hours_before >= 24 ? `≈ ${Math.floor(slab.hours_before / 24)} day${Math.floor(slab.hours_before / 24) !== 1 ? 's' : ''}` : '< 1 day'}
                      </p>
                    </div>
                    <div className="col-span-5">
                      <div className="flex items-center gap-2">
                        <Input
                          type="number" min="0" max="100"
                          value={slab.charge_percent}
                          onChange={(e) => updateCancellationSlab(index, 'charge_percent', e.target.value)}
                          onFocus={(e) => e.target.select()}
                          className="earms-input"
                          data-testid={`input-charge-${index}`}
                        />
                        <span className="text-sm text-slate-500">% charge</span>
                      </div>
                      <p className="text-xs text-green-600 mt-1 ml-1">
                        = {100 - slab.charge_percent}% refund
                      </p>
                    </div>
                    <div className="col-span-2">
                      <Button size="sm" variant="ghost" onClick={() => removeCancellationSlab(index)}
                        className="text-red-500 hover:text-red-600 hover:bg-red-50"
                        data-testid={`remove-slab-${index}`}>
                        <Trash size={18} />
                      </Button>
                    </div>
                  </div>
                ))}
            </div>
            <Button variant="outline" onClick={addCancellationSlab} className="w-full border-dashed" data-testid="add-slab-btn">
              <Plus size={18} className="mr-2" />
              Add Cancellation Slab
            </Button>
            <div className="p-4 bg-blue-50 rounded-xl mt-4">
              <h4 className="font-semibold text-blue-800 mb-2">Policy Preview</h4>
              <div className="space-y-1 text-sm">
                {formData.cancellation_policy
                  .sort((a, b) => b.hours_before - a.hours_before)
                  .map((slab, index, arr) => {
                    const nextSlab = arr[index + 1];
                    const rangeEnd = nextSlab ? nextSlab.hours_before + 1 : 0;
                    const refundPercent = 100 - slab.charge_percent;
                    const days = Math.floor(slab.hours_before / 24);
                    const nextDays = nextSlab ? Math.floor((nextSlab.hours_before + 1) / 24) : 0;
                    return (
                      <div key={index} className="flex justify-between">
                        <span className="text-slate-600">
                          {slab.hours_before === 0 ? "Less than minimum notice" :
                            nextSlab ? `${rangeEnd}-${slab.hours_before} hours (${nextDays}-${days} days)` :
                            `${slab.hours_before}+ hours (${days}+ days)`}
                        </span>
                        <span className={refundPercent === 100 ? "text-emerald-600 font-medium" : refundPercent === 0 ? "text-red-600 font-medium" : "text-amber-600 font-medium"}>
                          {refundPercent === 100 ? "Full Refund" : refundPercent === 0 ? "No Refund" : `${refundPercent}% Refund`}
                        </span>
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Room Configuration Info */}
      <Card className="earms-card" data-testid="room-config-section">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Buildings size={24} className="text-slate-500" weight="duotone" />
            Room Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="p-6 bg-blue-50 rounded-2xl text-center">
              <h3 className="font-semibold text-blue-800 mb-2">Cat I Rooms</h3>
              <p className="text-4xl font-bold text-blue-600">{settings?.cat_i_rooms_count || 6}</p>
              <p className="text-sm text-blue-600 mt-2">Total rooms</p>
            </div>
            <div className="p-6 bg-purple-50 rounded-2xl text-center">
              <h3 className="font-semibold text-purple-800 mb-2">Cat II Rooms</h3>
              <p className="text-4xl font-bold text-purple-600">{settings?.cat_ii_rooms_count || 9}</p>
              <p className="text-sm text-purple-600 mt-2">Total rooms</p>
            </div>
          </div>
          <div className="mt-6 p-4 bg-slate-50 rounded-xl">
            <div className="flex items-start gap-3">
              <Info size={20} className="text-slate-500 mt-0.5" />
              <div>
                <p className="font-medium text-slate-700">Room Count Configuration</p>
                <p className="text-sm text-slate-600 mt-1">
                  Total Rooms: {(settings?.cat_i_rooms_count || 6) + (settings?.cat_ii_rooms_count || 9)}
                </p>
                <p className="text-sm text-slate-500 mt-2">
                  To modify room counts, please contact the system administrator.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="sticky bottom-0 bg-white p-4 border-t-2 border-blue-200 shadow-lg rounded-t-xl">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <p className="text-sm text-slate-600">
            <Info size={16} className="inline mr-1" weight="fill" />
            Make sure to save your changes before leaving this page
          </p>
          <Button
            onClick={handleSave}
            disabled={saving}
            className="earms-btn-primary flex items-center gap-2 px-6 py-3 text-lg"
            data-testid="save-settings-btn"
          >
            {saving ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <FloppyDisk size={24} weight="fill" />
                Save Settings
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
