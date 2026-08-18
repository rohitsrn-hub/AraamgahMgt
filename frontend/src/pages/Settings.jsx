import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import RateSchedule from "@/components/RateSchedule";
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
    // Org category rates (room_rent/license_fee per category) now live on
    // the categories[] array below, edited in Room Categories — not here.
    // Non-Org stays a flat, category-independent rate, edited here.
    non_org_room_rent: settings?.non_org_room_rent || settings?.def_civ_room_rent || 570,
    non_org_license_fee: settings?.non_org_license_fee || settings?.def_civ_license_fee || 30,
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

  // formData's initial values are locked in at mount (useState only reads
  // its initializer once). The Non-Org rate specifically needs to track the
  // `settings` prop live: GET /settings resolves it to whichever rate is
  // effective TODAY, so the moment a scheduled rate change's date arrives —
  // or the moment a new one is scheduled/removed via the Rate Schedule
  // panel below — this screen would otherwise keep showing whatever was
  // true when it first mounted. Scoped to just this field, not the whole
  // form, so it can't clobber an admin's unsaved edits elsewhere.
  useEffect(() => {
    if (!settings) return;
    setFormData((prev) => ({
      ...prev,
      non_org_room_rent: settings.non_org_room_rent ?? prev.non_org_room_rent,
      non_org_license_fee: settings.non_org_license_fee ?? prev.non_org_license_fee,
    }));
  }, [settings?.non_org_room_rent, settings?.non_org_license_fee]);

  // Same staleness problem for categories: room_rent/license_fee per
  // category also resolve to today's effective rate server-side, and a
  // category can be added/edited elsewhere (e.g. after provisioning rooms
  // for a new wing) without this page remounting. Skipped while the admin
  // has unsaved local edits (categoriesDirty) so this can't clobber them.
  useEffect(() => {
    if (settings?.room_categories && !categoriesDirty) setCategories(settings.room_categories);
  }, [settings?.room_categories, categoriesDirty]);
  
  // P4: Room Categories Management
  const [categories, setCategories] = useState(
    settings?.room_categories || [
      { id: "cat-i", name: "Cat I", room_rent: 470, license_fee: 30, room_count: 6, prefix: "C1", capacity: 2 },
      { id: "cat-ii", name: "Cat II", room_rent: 385, license_fee: 15, room_count: 9, prefix: "C2", capacity: 2 }
    ]
  );
  // Guards the categories-resync effect below: don't overwrite local edits
  // the admin hasn't saved yet just because something elsewhere on the page
  // (e.g. Rate Schedule) triggered a settings refresh.
  const [categoriesDirty, setCategoriesDirty] = useState(false);

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
      { id: newId, name: "", room_rent: 0, license_fee: 0, room_count: 0, prefix: "", capacity: 2 }
    ]);
    setCategoriesDirty(true);
  };

  const updateCategory = (index, field, value) => {
    const updated = [...categories];
    updated[index] = { ...updated[index], [field]: value };
    setCategories(updated);
    setCategoriesDirty(true);
  };

  const removeCategory = (index) => {
    if (categories.length <= 1) {
      toast.error("At least one category is required");
      return;
    }
    setCategories(categories.filter((_, i) => i !== index));
    setCategoriesDirty(true);
  };

  const saveCategories = async () => {
    // Validate categories
    for (const cat of categories) {
      if (!cat.name || !cat.prefix) {
        toast.error("All categories must have a name and prefix");
        return;
      }
      if (cat.room_rent <= 0 || cat.license_fee < 0) {
        toast.error("Room rent must be greater than 0 and license fee cannot be negative");
        return;
      }
      if (!cat.capacity || cat.capacity <= 0) {
        toast.error("Room capacity must be greater than 0");
        return;
      }
    }

    setSaving(true);
    try {
      const res = await axios.put(`${API}/settings/categories`, categories);
      const created = res.data?.rooms_created || [];
      toast.success(
        created.length > 0
          ? `Room categories updated — created ${created.length} new room(s): ${created.join(", ")}`
          : "Room categories updated successfully!"
      );
      setCategoriesDirty(false);
      onUpdate();
    } catch (error) {
      console.error("Error saving categories:", error);
      toast.error(error.response?.data?.detail || "Failed to save categories");
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
                    <Label className="text-xs">Room Rent (₹/night) *</Label>
                    <Input
                      type="number"
                      min="0"
                      value={cat.room_rent}
                      onChange={(e) => updateCategory(idx, "room_rent", parseFloat(e.target.value) || 0)}
                      onFocus={(e) => e.target.select()}
                      className="earms-input mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">License Fee (₹/night) *</Label>
                    <Input
                      type="number"
                      min="0"
                      value={cat.license_fee}
                      onChange={(e) => updateCategory(idx, "license_fee", parseFloat(e.target.value) || 0)}
                      onFocus={(e) => e.target.select()}
                      className="earms-input mt-1"
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      Total = ₹{(cat.room_rent || 0) + (cat.license_fee || 0)}/night for Org guests. Non-Org guests are billed a flat rate below, regardless of category.
                    </p>
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
              onClick={() => {
                setCategories(settings?.room_categories || categories);
                setCategoriesDirty(false);
              }}
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

      {/* Non-Org Rate — flat, applies regardless of room category */}
      <Card className="earms-card" data-testid="non-org-rate-section">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Percent size={24} className="text-blue-500" weight="duotone" />
            Non-Org Rate
          </CardTitle>
          <p className="text-sm text-slate-500">
            Flat rate for Non-Org guests, the same regardless of which room category they stay in.
            Org guest rates are set per category above, in Room Categories.
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 max-w-md">
            <div>
              <Label className="text-xs text-slate-500">Room Rent (₹)</Label>
              <Input type="number" value={formData.non_org_room_rent} onChange={(e) => setFormData({...formData, non_org_room_rent: parseFloat(e.target.value) || 0})} onFocus={(e) => e.target.select()} className="earms-input mt-1" data-testid="input-non_org_room_rent" />
            </div>
            <div>
              <Label className="text-xs text-slate-500">License Fee (₹)</Label>
              <Input type="number" value={formData.non_org_license_fee} onChange={(e) => setFormData({...formData, non_org_license_fee: parseFloat(e.target.value) || 0})} onFocus={(e) => e.target.select()} className="earms-input mt-1" data-testid="input-non_org_license_fee" />
            </div>
          </div>
          <div className="text-xs font-semibold mt-3 p-2 bg-orange-50 text-orange-700 rounded max-w-md">
            Total = ₹{(formData.non_org_room_rent || 0) + (formData.non_org_license_fee || 0)}/night
          </div>
        </CardContent>
      </Card>

      {/* Rate Schedule (date-versioned future rate changes) */}
      <RateSchedule onUpdate={onUpdate} />

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
