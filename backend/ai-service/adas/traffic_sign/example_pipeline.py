"""
Quick Start Example - Full Pipeline Demo
Demonstrating TV1 → TV2 → TV3 → TV4 → TV5
"""

# ============================================================================
# TV1: Traffic Sign Recognition Input
# ============================================================================
print("=" * 70)
print("TV1: Traffic Sign Recognition Input")
print("=" * 70)

from adas.traffic_sign import SignInputService
from models import DrivingRuleData, SpeedLimitState

# Initialize TV1 Service
tv1_service = SignInputService(confidence_threshold=0.5)

# Simulate YOLO detection results
raw_detections = [
    {
        "class_id": 38,
        "confidence": 0.95,
        "bbox": [150, 80, 240, 190]
    },
    {
        "class_id": 2,
        "confidence": 0.92,
        "bbox": [200, 100, 300, 220]
    },
    {
        "class_id": 38,
        "confidence": 0.30,  # Will be filtered (confidence < 0.5)
        "bbox": [120, 150, 180, 240]
    }
]

# Process batch detections
print("\n[TV1] Processing batch detections...")
standard_data_list = tv1_service.process_batch_detections(
    raw_detections=raw_detections,
    frame_id=120,
    tracking_ids=[1, 2, 3]
)

print(f"\n[TV1] Processed {len(standard_data_list)} valid detections:")
for data in standard_data_list:
    print(f"  - Frame {data.frame_id}: {data.class_name} (confidence: {data.confidence})")

# Output from TV1 (input to TV2)
tv1_output = standard_data_list
print(f"\n[TV1] Output: {len(tv1_output)} StandardTrafficSignData objects → TV2")


# ============================================================================
# TV2: Rule Engine (SIMULATED)
# In real implementation, TV2 would process TV1 output and generate DrivingRuleData
# ============================================================================
print("\n" + "=" * 70)
print("TV2: Rule Engine (SIMULATED)")
print("=" * 70)

# Simulated TV2 output - DrivingRuleData
tv2_output = [
    DrivingRuleData(
        frame_id=120,
        tracking_id=1,
        rule="SET_SPEED_LIMIT",
        speed_limit=50,
        message="Gioi han toc do 50kmh"
    ),
    DrivingRuleData(
        frame_id=120,
        tracking_id=2,
        rule="NO_ENTRY",
        message="Cam di nguoc chieu"
    )
]

print(f"\n[TV2] Generated {len(tv2_output)} DrivingRuleData objects:")
for rule in tv2_output:
    print(f"  - {rule.rule}: {rule.message}")


# ============================================================================
# TV3: Speed Limit State Management
# ============================================================================
print("\n" + "=" * 70)
print("TV3: Speed Limit State Management")
print("=" * 70)

from adas.traffic_sign import SpeedLimitService

tv3_service = SpeedLimitService()

print("\n[TV3] Processing driving rules...")
for rule in tv2_output:
    if rule.rule == "SET_SPEED_LIMIT":
        state = tv3_service.process_driving_rule(rule)
        if state:
            print(f"  ✓ Speed limit updated: {state.speed_limit} km/h")
            print(f"    Status: {state.status}")
            print(f"    Source: {state.source}")
            tv3_output = state

# Get current state
current_state = tv3_service.get_current_state()
print(f"\n[TV3] Current Speed Limit State:")
print(f"  - Speed Limit: {current_state.speed_limit} km/h")
print(f"  - Status: {current_state.status}")
print(f"  - Updated: {current_state.updated_at.isoformat()}")


# ============================================================================
# TV4: Traffic Warning Decision Engine
# ============================================================================
print("\n" + "=" * 70)
print("TV4: Traffic Warning Decision Engine")
print("=" * 70)

from adas.traffic_sign import WarningDecisionService

tv4_service = WarningDecisionService()

print("\n[TV4] Processing driving rules with context...")
tv4_warnings = []

for rule in tv2_output:
    warning = tv4_service.process_driving_rule(
        driving_rule=rule,
        speed_limit_state=current_state
    )
    if warning:
        tv4_warnings.append(warning)
        print(f"  ✓ Warning created:")
        print(f"    - Type: {warning.type}")
        print(f"    - Level: {warning.level}")
        print(f"    - Priority: {warning.priority}/100")
        print(f"    - Duration: {warning.duration}s")

# Get active warnings
active = tv4_service.get_active_warnings()
print(f"\n[TV4] Active warnings: {len(active)}")

# Publish to TV5
tv4_output = tv4_service.publish_warnings_for_tv5()
print(f"\n[TV4] Output: {len(tv4_output)} TrafficWarning objects → TV5")


# ============================================================================
# TV5: Warning Manager
# ============================================================================
print("\n" + "=" * 70)
print("TV5: Warning Manager")
print("=" * 70)

from adas.traffic_sign import WarningManager

tv5_manager = WarningManager()

print("\n[TV5] Processing warnings...")
queued_events = []

for warning in tv4_output:
    event = tv5_manager.process_warning(warning)
    if event:
        queued_events.append(event)
        print(f"  ✓ Warning queued:")
        print(f"    - Event ID: {event.event_id}")
        print(f"    - Type: {event.warning.type}")
        print(f"    - Status: {event.status}")

# Get queue status
queue_status = tv5_manager.get_queue_status()
print(f"\n[TV5] Queue Status:")
print(f"  - Queue Size: {queue_status['size']}/{queue_status['max_size']}")
print(f"  - Is Full: {queue_status['is_full']}")

# Simulate displaying warnings
print("\n[TV5] Displaying warnings...")
for i in range(min(2, len(queued_events))):
    event = tv5_manager.get_next_warning()
    if event:
        print(f"  → Displaying: {event.warning.type} ({event.warning.level})")
        print(f"    Message: {event.warning.message}")

# Get manager status
manager_status = tv5_manager.get_manager_status()
print(f"\n[TV5] Manager Status:")
if manager_status['current_warning']:
    print(f"  - Currently Displaying: {manager_status['current_warning']['type']}")
print(f"  - Queue Size: {manager_status['queue']['size']}")
print(f"  - History Count: {len(manager_status['history'])}")


# ============================================================================
# Full Pipeline Summary
# ============================================================================
print("\n" + "=" * 70)
print("FULL PIPELINE SUMMARY")
print("=" * 70)

print("""
TV1 Input:  3 raw YOLO detections
  ↓ Filter (confidence)
TV1 Output: 2 StandardTrafficSignData
  ↓
TV2 Output: 2 DrivingRuleData (SET_SPEED_LIMIT, NO_ENTRY)
  ↓
TV3 Process: 1 SET_SPEED_LIMIT rule
TV3 Output:  SpeedLimitState (50 km/h)
  ↓ (combined with TV2 output)
TV4 Decision: NO_ENTRY → Generate Warning
TV4 Output: 1 TrafficWarning (HIGH priority)
  ↓
TV5 Queue:  1 WarningEvent in queue
TV5 Display: Currently showing 1 warning

Pipeline Status: ✓ ACTIVE
Warnings Processed: 1
Queue Size: 0/10
""")

print("=" * 70)
print("Pipeline demo completed successfully!")
print("=" * 70)
