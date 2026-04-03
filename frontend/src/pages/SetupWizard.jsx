import { useState } from "react";
import axios from "axios";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Buildings, CurrencyInr, Image, Rocket } from "@phosphor-icons/react";

const DEFAULT_FMN_1 = "https://images.unsplash.com/photo-1765555648802-53235276a40b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwyfHxzaGllbGQlMjBlbWJsZW18ZW58MHx8fHwxNzc1MDcwOTU4fDA&ixlib=rb-4.1.0&q=85";
const DEFAULT_FMN_2 = "https://images.unsplash.com/photo-1771456915291-58f0dee5b404?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwxfHxzaGllbGQlMjBlbWJsZW18ZW58MHx8fHwxNzc1MDcwOTU4fDA&ixlib=rb-4.1.0&q=85";

export default function SetupWizard({ onComplete }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    fmn_sign_1_url: "",
    fmn_sign_2_url: "",
    cat_i_rooms_count: 6,
    cat_ii_rooms_count: 9,
    cat_i_rate: 500,
    cat_ii_rate: 300,
  });

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const payload = {
        ...formData,
        fmn_sign_1_url: formData.fmn_sign_1_url || DEFAULT_FMN_1,
        fmn_sign_2_url: formData.fmn_sign_2_url || DEFAULT_FMN_2,
      };
      await axios.post(`${API}/settings/setup`, payload);
      toast.success("Setup completed successfully!");
      onComplete();
    } catch (error) {
      console.error("Setup error:", error);
      toast.error("Setup failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => setStep((s) => Math.min(s + 1, 3));
  const prevStep = () => setStep((s) => Math.max(s - 1, 1));

  return (
    <div className="setup-wizard" data-testid="setup-wizard">
      <div className="setup-card animate-fade-in">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-slate-800 mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Welcome to E-ARMS
          </h1>
          <p className="text-slate-500">
            ECSAG Automated Room Management System
          </p>
        </div>

        {/* Progress indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`w-3 h-3 rounded-full transition-all ${
                s === step ? "bg-blue-500 w-8" : s < step ? "bg-blue-500" : "bg-slate-200"
              }`}
            />
          ))}
        </div>

        {/* Step 1: Formation Signs */}
        {step === 1 && (
          <div className="space-y-6 animate-fade-in" data-testid="setup-step-1">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-blue-100 rounded-xl">
                <Image size={24} className="text-blue-600" weight="duotone" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-800">Formation Signs</h2>
                <p className="text-sm text-slate-500">Upload your formation emblems (optional)</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <Label htmlFor="fmn1" className="text-slate-600 mb-2 block">
                  Formation Sign 1 (Left)
                </Label>
                <Input
                  id="fmn1"
                  type="url"
                  placeholder="Image URL (optional)"
                  value={formData.fmn_sign_1_url}
                  onChange={(e) => handleChange("fmn_sign_1_url", e.target.value)}
                  className="earms-input"
                  data-testid="input-fmn-sign-1"
                />
                <div className="mt-3 p-4 bg-slate-50 rounded-xl flex items-center justify-center">
                  <img
                    src={formData.fmn_sign_1_url || DEFAULT_FMN_1}
                    alt="Preview 1"
                    className="h-20 w-20 object-contain"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="fmn2" className="text-slate-600 mb-2 block">
                  Formation Sign 2 (Right)
                </Label>
                <Input
                  id="fmn2"
                  type="url"
                  placeholder="Image URL (optional)"
                  value={formData.fmn_sign_2_url}
                  onChange={(e) => handleChange("fmn_sign_2_url", e.target.value)}
                  className="earms-input"
                  data-testid="input-fmn-sign-2"
                />
                <div className="mt-3 p-4 bg-slate-50 rounded-xl flex items-center justify-center">
                  <img
                    src={formData.fmn_sign_2_url || DEFAULT_FMN_2}
                    alt="Preview 2"
                    className="h-20 w-20 object-contain"
                  />
                </div>
              </div>
            </div>

            <p className="text-sm text-slate-400 text-center">
              Leave empty to use default placeholder images
            </p>
          </div>
        )}

        {/* Step 2: Room Configuration */}
        {step === 2 && (
          <div className="space-y-6 animate-fade-in" data-testid="setup-step-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-emerald-100 rounded-xl">
                <Buildings size={24} className="text-emerald-600" weight="duotone" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-800">Room Configuration</h2>
                <p className="text-sm text-slate-500">Configure your room categories</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="p-6 bg-blue-50 rounded-2xl">
                <h3 className="font-semibold text-blue-800 mb-4">Cat I Rooms</h3>
                <Label htmlFor="cat1count" className="text-slate-600 mb-2 block">
                  Number of Rooms
                </Label>
                <Input
                  id="cat1count"
                  type="number"
                  min="1"
                  max="39"
                  value={formData.cat_i_rooms_count}
                  onChange={(e) => handleChange("cat_i_rooms_count", parseInt(e.target.value) || 1)}
                  className="earms-input"
                  data-testid="input-cat-i-count"
                />
              </div>

              <div className="p-6 bg-purple-50 rounded-2xl">
                <h3 className="font-semibold text-purple-800 mb-4">Cat II Rooms</h3>
                <Label htmlFor="cat2count" className="text-slate-600 mb-2 block">
                  Number of Rooms
                </Label>
                <Input
                  id="cat2count"
                  type="number"
                  min="1"
                  max="39"
                  value={formData.cat_ii_rooms_count}
                  onChange={(e) => handleChange("cat_ii_rooms_count", parseInt(e.target.value) || 1)}
                  className="earms-input"
                  data-testid="input-cat-ii-count"
                />
              </div>
            </div>

            <div className="p-4 bg-amber-50 rounded-xl text-center">
              <p className="text-amber-800 font-medium">
                Total Rooms: {formData.cat_i_rooms_count + formData.cat_ii_rooms_count}
              </p>
              <p className="text-sm text-amber-600">Scalable up to 39 rooms</p>
            </div>
          </div>
        )}

        {/* Step 3: Room Rates */}
        {step === 3 && (
          <div className="space-y-6 animate-fade-in" data-testid="setup-step-3">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-amber-100 rounded-xl">
                <CurrencyInr size={24} className="text-amber-600" weight="duotone" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-800">Room Rates</h2>
                <p className="text-sm text-slate-500">Set daily rates for each category</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="p-6 bg-blue-50 rounded-2xl">
                <h3 className="font-semibold text-blue-800 mb-4">Cat I Rate</h3>
                <Label htmlFor="cat1rate" className="text-slate-600 mb-2 block">
                  Daily Rate (₹)
                </Label>
                <Input
                  id="cat1rate"
                  type="number"
                  min="0"
                  value={formData.cat_i_rate}
                  onChange={(e) => handleChange("cat_i_rate", parseFloat(e.target.value) || 0)}
                  className="earms-input"
                  data-testid="input-cat-i-rate"
                />
              </div>

              <div className="p-6 bg-purple-50 rounded-2xl">
                <h3 className="font-semibold text-purple-800 mb-4">Cat II Rate</h3>
                <Label htmlFor="cat2rate" className="text-slate-600 mb-2 block">
                  Daily Rate (₹)
                </Label>
                <Input
                  id="cat2rate"
                  type="number"
                  min="0"
                  value={formData.cat_ii_rate}
                  onChange={(e) => handleChange("cat_ii_rate", parseFloat(e.target.value) || 0)}
                  className="earms-input"
                  data-testid="input-cat-ii-rate"
                />
              </div>
            </div>

            <p className="text-sm text-slate-400 text-center">
              Rates can be edited later in Settings
            </p>
          </div>
        )}

        {/* Navigation buttons */}
        <div className="flex justify-between mt-8 pt-6 border-t border-slate-100">
          {step > 1 ? (
            <Button
              variant="outline"
              onClick={prevStep}
              className="h-12 px-6 rounded-xl"
              data-testid="setup-prev-btn"
            >
              Back
            </Button>
          ) : (
            <div />
          )}

          {step < 3 ? (
            <Button
              onClick={nextStep}
              className="h-12 px-8 bg-blue-500 hover:bg-blue-600 rounded-xl"
              data-testid="setup-next-btn"
            >
              Continue
            </Button>
          ) : (
            <Button
              onClick={handleSubmit}
              disabled={loading}
              className="h-12 px-8 bg-emerald-500 hover:bg-emerald-600 rounded-xl flex items-center gap-2"
              data-testid="setup-complete-btn"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Rocket size={20} weight="fill" />
                  Complete Setup
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
