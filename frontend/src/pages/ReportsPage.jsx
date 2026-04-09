import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChartBar, Bed, Users, FileText } from "@phosphor-icons/react";
import MonthlySummaryTab from "./reports/MonthlySummaryTab";
import RoomOccupancyTab from "./reports/RoomOccupancyTab";

export default function ReportsPage({ settings }) {
  const [activeTab, setActiveTab] = useState("monthly");

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
          <ChartBar size={36} weight="duotone" className="text-blue-500" />
          Reports
        </h1>
        <p className="text-slate-500 mt-1">Comprehensive reports and analytics</p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 h-auto bg-gradient-to-r from-blue-50 to-indigo-50 p-1 rounded-xl shadow-sm">
          <TabsTrigger 
            value="monthly"
            className="data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200 py-3 px-4 rounded-lg font-semibold"
          >
            <ChartBar size={20} className="mr-2" weight="fill" />
            <span className="hidden sm:inline">Monthly Summary</span>
            <span className="sm:hidden">Monthly</span>
          </TabsTrigger>
          
          <TabsTrigger 
            value="occupancy"
            className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200 py-3 px-4 rounded-lg font-semibold"
          >
            <Bed size={20} className="mr-2" weight="fill" />
            <span className="hidden sm:inline">Room Occupancy</span>
            <span className="sm:hidden">Occupancy</span>
          </TabsTrigger>
          
          <TabsTrigger 
            value="allotment"
            className="data-[state=active]:bg-purple-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200 py-3 px-4 rounded-lg font-semibold opacity-50 cursor-not-allowed"
            disabled
          >
            <FileText size={20} className="mr-2" weight="fill" />
            <span className="hidden sm:inline">Room Allotment</span>
            <span className="sm:hidden">Allotment</span>
          </TabsTrigger>
          
          <TabsTrigger 
            value="guests"
            className="data-[state=active]:bg-teal-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200 py-3 px-4 rounded-lg font-semibold opacity-50 cursor-not-allowed"
            disabled
          >
            <Users size={20} className="mr-2" weight="fill" />
            <span className="hidden sm:inline">Guest Details</span>
            <span className="sm:hidden">Guests</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab Content - Monthly Summary */}
        <TabsContent value="monthly" className="mt-6 bg-blue-50/30 p-6 rounded-xl">
          <MonthlySummaryTab settings={settings} />
        </TabsContent>

        {/* Tab Content - Room Occupancy */}
        <TabsContent value="occupancy" className="mt-6 bg-indigo-50/30 p-6 rounded-xl">
          <RoomOccupancyTab settings={settings} />
        </TabsContent>

        {/* Tab Content - Room Allotment (Coming Soon) */}
        <TabsContent value="allotment" className="mt-6 bg-purple-50/30 p-6 rounded-xl">
          <div className="text-center py-12 text-slate-500">
            <FileText size={48} className="mx-auto mb-4 opacity-50" />
            <p className="font-medium">Room Allotment Report - Coming Soon</p>
          </div>
        </TabsContent>

        {/* Tab Content - Guest Details (Coming Soon) */}
        <TabsContent value="guests" className="mt-6 bg-teal-50/30 p-6 rounded-xl">
          <div className="text-center py-12 text-slate-500">
            <Users size={48} className="mx-auto mb-4 opacity-50" />
            <p className="font-medium">Guest Details Report - Coming Soon</p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
