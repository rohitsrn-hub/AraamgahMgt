import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format, parseISO, differenceInDays } from 'date-fns';
import { toast } from 'sonner';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { CalendarBlank, CheckCircle, ArrowRight, Pencil } from '@phosphor-icons/react';
import { fmtINR } from "@/utils/formatters";
import { getRoomRate } from "@/utils/rateUtils";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Color palette for different rooms
const ROOM_COLORS = [
  'bg-blue-100 text-blue-800 border-blue-300',
  'bg-green-100 text-green-800 border-green-300',
  'bg-purple-100 text-purple-800 border-purple-300',
  'bg-orange-100 text-orange-800 border-orange-300',
  'bg-pink-100 text-pink-800 border-pink-300',
  'bg-cyan-100 text-cyan-800 border-cyan-300',
  'bg-amber-100 text-amber-800 border-amber-300',
  'bg-emerald-100 text-emerald-800 border-emerald-300',
];

const RoomSegmentSelector = ({ 
  checkInDate, 
  checkOutDate, 
  numRooms, 
  isOrg,
  settings,
  onAccept,
  onCancel,
  excludeBookingId = null
}) => {
  const [loading, setLoading] = useState(true);
  const [optimalCombination, setOptimalCombination] = useState(null);
  const [customizing, setCustomizing] = useState(false);
  const [customSegments, setCustomSegments] = useState([]);
  const [availableRoomsPerNight, setAvailableRoomsPerNight] = useState({});
  const [roomColorMap, setRoomColorMap] = useState({});
  const [showManualSelector, setShowManualSelector] = useState(false);
  const [selectedNight, setSelectedNight] = useState(null);

  useEffect(() => {
    if (checkInDate && checkOutDate && numRooms > 0) {
      fetchOptimalCombination();
    }
  }, [checkInDate, checkOutDate, numRooms]);

  const fetchOptimalCombination = async () => {
    setLoading(true);
    try {
      const params = {
        check_in: format(checkInDate, 'yyyy-MM-dd'),
        check_out: format(checkOutDate, 'yyyy-MM-dd'),
        num_rooms: numRooms
      };
      
      if (excludeBookingId) {
        params.exclude_booking_id = excludeBookingId;
      }

      const response = await axios.post(`${API}/rooms/find-optimal-combination`, null, { params });
      
      if (response.data.availability_status === 'insufficient') {
        toast.error(response.data.message);
        setOptimalCombination(null);
      } else {
        setOptimalCombination(response.data);
        setCustomSegments(response.data.optimal_combination);
        assignRoomColors(response.data.optimal_combination);
        
        // Fetch available rooms for each night (for manual override)
        await fetchAvailableRoomsPerNight();
      }
    } catch (error) {
      console.error('Error fetching optimal combination:', error);
      toast.error('Failed to find room combination');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableRoomsPerNight = async () => {
    try {
      const nights = differenceInDays(checkOutDate, checkInDate);
      const roomsPerNight = {};

      for (let i = 0; i < nights; i++) {
        const nightDate = new Date(checkInDate);
        nightDate.setDate(nightDate.getDate() + i);
        const nextDate = new Date(nightDate);
        nextDate.setDate(nextDate.getDate() + 1);

        const params = {
          check_in: format(nightDate, 'yyyy-MM-dd'),
          check_out: format(nextDate, 'yyyy-MM-dd')
        };

        if (excludeBookingId) {
          params.exclude_booking_id = excludeBookingId;
        }

        const response = await axios.get(`${API}/rooms/available`, { params });
        roomsPerNight[format(nightDate, 'yyyy-MM-dd')] = response.data;
      }

      setAvailableRoomsPerNight(roomsPerNight);
    } catch (error) {
      console.error('Error fetching available rooms per night:', error);
    }
  };

  const assignRoomColors = (segments) => {
    const colorMap = {};
    let colorIndex = 0;
    
    segments.forEach(segment => {
      segment.rooms.forEach(room => {
        if (!colorMap[room.id]) {
          colorMap[room.id] = ROOM_COLORS[colorIndex % ROOM_COLORS.length];
          colorIndex++;
        }
      });
    });
    
    setRoomColorMap(colorMap);
  };

  const calculateTotalCost = (segments) => {
    let total = 0;

    segments.forEach(segment => {
      segment.rooms.forEach(room => {
        // Resolved by check-in date and the room's own category (any
        // configured category, not just Cat I/Cat II) via the same shared
        // resolver every other rate preview in the app uses — this used to
        // read the legacy cat_i_rate/cat_ii_rate settings fields directly
        // (not edited by Settings since the rent/license-fee split), so
        // this preview could disagree with what actually gets billed.
        const { rent, licenseFee } = getRoomRate(settings, checkInDate, isOrg, room.category);
        total += rent + licenseFee;
      });
    });

    return total;
  };

  const handleAcceptRecommendation = () => {
    onAccept({
      room_segments: optimalCombination.optimal_combination,
      has_room_changes: optimalCombination.total_room_changes > 0,
      total_amount: calculateTotalCost(optimalCombination.optimal_combination)
    });
  };

  const handleAcceptCustom = () => {
    onAccept({
      room_segments: customSegments,
      has_room_changes: checkForRoomChanges(customSegments),
      total_amount: calculateTotalCost(customSegments)
    });
  };

  const checkForRoomChanges = (segments) => {
    for (let i = 1; i < segments.length; i++) {
      const prevRooms = segments[i - 1].rooms.map(r => r.id).sort().join(',');
      const currRooms = segments[i].rooms.map(r => r.id).sort().join(',');
      if (prevRooms !== currRooms) return true;
    }
    return false;
  };

  const handleManualRoomSelection = (nightDate, selectedRooms) => {
    const updatedSegments = customSegments.map(segment => {
      if (segment.night_date === nightDate) {
        return { ...segment, rooms: selectedRooms };
      }
      return segment;
    });
    
    setCustomSegments(updatedSegments);
    setShowManualSelector(false);
    setSelectedNight(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-slate-600">Finding optimal room combination...</p>
        </div>
      </div>
    );
  }

  if (!optimalCombination || optimalCombination.availability_status === 'insufficient') {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 font-semibold">Insufficient room availability</p>
        <p className="text-slate-600 text-sm mt-2">Please select different dates or reduce number of rooms</p>
      </div>
    );
  }

  const totalCost = calculateTotalCost(customizing ? customSegments : optimalCombination.optimal_combination);
  const displaySegments = customizing ? customSegments : optimalCombination.optimal_combination;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center gap-2">
          <CalendarBlank size={24} className="text-blue-600" />
          <div>
            <h3 className="font-semibold text-blue-900">
              {customizing ? 'Custom Room Selection' : 'Recommended Room Combination'}
            </h3>
            <p className="text-sm text-blue-700">
              {optimalCombination.total_room_changes === 0 
                ? '✓ No room changes needed - same rooms for entire stay' 
                : `⚠️ ${optimalCombination.total_room_changes} room change(s) during stay`}
            </p>
          </div>
        </div>
        {!customizing && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCustomizing(true)}
            className="flex items-center gap-2"
          >
            <Pencil size={16} />
            Customize
          </Button>
        )}
      </div>

      {/* Nightly Room Assignment Grid */}
      <div className="border rounded-lg overflow-hidden">
        <div className="bg-slate-100 grid grid-cols-12 gap-2 p-3 font-semibold text-sm border-b">
          <div className="col-span-2">Night Date</div>
          <div className="col-span-8">Assigned Rooms</div>
          <div className="col-span-2 text-right">Status</div>
        </div>
        
        {displaySegments.map((segment, index) => {
          const prevSegment = index > 0 ? displaySegments[index - 1] : null;
          const hasChange = prevSegment && 
            prevSegment.rooms.map(r => r.id).sort().join(',') !== 
            segment.rooms.map(r => r.id).sort().join(',');

          return (
            <div 
              key={segment.night_date}
              className={`grid grid-cols-12 gap-2 p-3 border-b last:border-b-0 hover:bg-slate-50 ${
                hasChange ? 'bg-amber-50' : ''
              }`}
            >
              <div className="col-span-2 flex flex-col">
                <span className="font-medium text-sm">
                  {format(parseISO(segment.night_date), 'MMM dd')}
                </span>
                <span className="text-xs text-slate-500">
                  {format(parseISO(segment.night_date), 'EEEE')}
                </span>
              </div>
              
              <div className="col-span-8 flex flex-wrap gap-2">
                {segment.rooms.map(room => (
                  <div
                    key={room.id}
                    className={`px-3 py-1 rounded-md border text-sm font-medium ${roomColorMap[room.id]}`}
                  >
                    {room.room_number} ({room.category})
                  </div>
                ))}
                {customizing && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelectedNight(segment.night_date);
                      setShowManualSelector(true);
                    }}
                    className="text-xs"
                  >
                    <Pencil size={14} className="mr-1" />
                    Change
                  </Button>
                )}
              </div>
              
              <div className="col-span-2 text-right">
                {hasChange ? (
                  <Badge className="bg-amber-100 text-amber-800 border-amber-300">
                    <ArrowRight size={14} className="mr-1" />
                    Change
                  </Badge>
                ) : (
                  <Badge className="bg-green-100 text-green-800 border-green-300">
                    <CheckCircle size={14} className="mr-1" />
                    Same
                  </Badge>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Cost Summary */}
      <div className="p-4 bg-slate-50 rounded-lg border">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-sm text-slate-600">Total Cost</p>
            <p className="text-xs text-slate-500 mt-1">
              {displaySegments.length} night(s) × {numRooms} room(s)
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-slate-900">{fmtINR(totalCost, 0)}</p>
            <p className="text-xs text-slate-500">
              {isOrg ? 'Organization Rate' : 'Non-Organization Rate'}
            </p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 justify-end">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        {customizing ? (
          <>
            <Button variant="outline" onClick={() => {
              setCustomizing(false);
              setCustomSegments(optimalCombination.optimal_combination);
            }}>
              Reset to Recommended
            </Button>
            <Button onClick={handleAcceptCustom} className="bg-blue-500 hover:bg-blue-600">
              Accept Custom Selection
            </Button>
          </>
        ) : (
          <Button onClick={handleAcceptRecommendation} className="bg-blue-500 hover:bg-blue-600">
            <CheckCircle size={18} className="mr-2" />
            Accept Recommendation
          </Button>
        )}
      </div>

      {/* Manual Room Selector Dialog */}
      <Dialog open={showManualSelector} onOpenChange={setShowManualSelector}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Select Rooms for {selectedNight && format(parseISO(selectedNight), 'MMMM dd, yyyy')}</DialogTitle>
          </DialogHeader>
          
          {selectedNight && (
            <ManualRoomSelector
              nightDate={selectedNight}
              availableRooms={availableRoomsPerNight[selectedNight] || []}
              currentSelection={customSegments.find(s => s.night_date === selectedNight)?.rooms || []}
              numRoomsNeeded={numRooms}
              onConfirm={(selectedRooms) => handleManualRoomSelection(selectedNight, selectedRooms)}
              onCancel={() => setShowManualSelector(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Manual Room Selector Component
const ManualRoomSelector = ({ nightDate, availableRooms, currentSelection, numRoomsNeeded, onConfirm, onCancel }) => {
  const [selectedRooms, setSelectedRooms] = useState(currentSelection);

  const toggleRoom = (room) => {
    const isSelected = selectedRooms.some(r => r.id === room.id);
    
    if (isSelected) {
      setSelectedRooms(selectedRooms.filter(r => r.id !== room.id));
    } else if (selectedRooms.length < numRoomsNeeded) {
      setSelectedRooms([...selectedRooms, room]);
    } else {
      toast.error(`You can only select ${numRoomsNeeded} room(s)`);
    }
  };

  return (
    <div className="space-y-4">
      <div className="text-sm text-slate-600">
        Select {numRoomsNeeded} room(s) for this night ({selectedRooms.length}/{numRoomsNeeded} selected)
      </div>
      
      <div className="grid grid-cols-4 gap-3 max-h-96 overflow-y-auto p-2">
        {availableRooms.map(room => {
          const isSelected = selectedRooms.some(r => r.id === room.id);
          
          return (
            <div
              key={room.id}
              onClick={() => toggleRoom(room)}
              className={`p-3 border-2 rounded-lg cursor-pointer text-center transition-all ${
                isSelected 
                  ? 'border-blue-500 bg-blue-50 shadow-md' 
                  : 'border-slate-200 hover:border-blue-300 hover:bg-slate-50'
              }`}
            >
              <div className="font-semibold text-lg">{room.room_number}</div>
              <div className="text-xs text-slate-600 mt-1">{room.category}</div>
              {isSelected && (
                <CheckCircle size={20} className="text-blue-600 mx-auto mt-2" weight="fill" />
              )}
            </div>
          );
        })}
      </div>
      
      <DialogFooter>
        <Button variant="outline" onClick={onCancel}>Cancel</Button>
        <Button 
          onClick={() => onConfirm(selectedRooms)}
          disabled={selectedRooms.length !== numRoomsNeeded}
          className="bg-blue-500 hover:bg-blue-600"
        >
          Confirm Selection
        </Button>
      </DialogFooter>
    </div>
  );
};

export default RoomSegmentSelector;
