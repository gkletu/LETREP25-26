#include <stdio.h>
#include <iostream>
#include <vector>
#include "pubSysCls.h"

using namespace sFnd;

// Globals so multiple functions can use them
static SysManager* g_mgr = nullptr;
static INode*      g_node = nullptr;

// Helper declarations
void msgUser(const char* msg);
void printNodeInfo(INode& node);
bool moveAtVelocity(INode&, int);
bool moveDistance(INode& node, int target, bool targetIsAbsolute);

// Exported: initialize system and node

#include <unistd.h> // Required for usleep

//extern "C" int setup() {
    //printf("Position Moves starting.\n");
    //try {
        //g_mgr = SysManager::Instance();
        
        //// Close any existing connections to clear the port
        //g_mgr->PortsClose(); 
        
        //// Define the port - use Net 0 and the path we verified
        //g_mgr->ComHubPort(0, "/dev/ttyXRUSB0");
        
        //// Open the port. We use a try/catch here in case the OS has it locked.
        //try {
            //g_mgr->PortsOpen(1); 
        //} catch (mnErr& e) {
            //printf("First open attempt failed: %s. Retrying...\n", e.ErrorMsg);
            //usleep(500000); // Wait 0.5s
            //g_mgr->PortsOpen(1);
        //}

        //IPort& port = g_mgr->Ports(0);

        //// Wait for the SC-Hub to find the motor nodes
        //// This is the most common place where it fails on Raspberry Pi
        //int retry = 0;
        //while (port.NodeCount() == 0 && retry < 30) {
            //usleep(100000); // Wait 100ms
            //retry++;
        //}

        //if (port.NodeCount() == 0) {
            //printf("Error: Port opened, but no motors were detected.\n");
            //return 1;
        //}

        //g_node = &port.Nodes(0);
        //g_node->Status.AlertsClear();
        //g_node->Motion.NodeStopClear();
        //g_node->EnableReq(true);

        //printf("Node found: %s. Enabling...\n", g_node->Info.UserID.Value());
        //return 0;
    //}
    //catch (mnErr& e) {
        //printf("Caught Error: %s\n", e.ErrorMsg);
        //return 1;
    //}
//}

// initialize and home system
extern "C" int setup_and_home(int timeout_ms) {
    printf("Initializing System and Starting Hardware-Controlled Homing...\n");
    
    try {
        g_mgr = SysManager::Instance();
        
        // 1. Port Initialization
        g_mgr->PortsClose(); 
        g_mgr->ComHubPort(0, "/dev/ttyXRUSB0");
        
        try {
            g_mgr->PortsOpen(1); 
        } catch (mnErr& e) {
            printf("Port open failed: %s. Retrying...\n", e.ErrorMsg);
            usleep(500000); 
            g_mgr->PortsOpen(1);
        }

        IPort& port = g_mgr->Ports(0);
        int retry = 0;
        while (port.NodeCount() == 0 && retry < 30) {
            usleep(100000);
            retry++;
        }

        if (port.NodeCount() == 0) {
            printf("Error: No motors detected on /dev/ttyXRUSB0\n");
            return 1;
        }

        // 2. Node Preparation
        g_node = &port.Nodes(0);
        g_node->Status.AlertsClear();
        g_node->Motion.NodeStopClear();
        g_node->EnableReq(true);

        // Wait for motor to enable (max 5s)
        double enableTimeout = g_mgr->TimeStampMsec() + 5000;
        while (!g_node->Motion.IsReady()) {
            if (g_mgr->TimeStampMsec() > enableTimeout) {
                printf("Error: Motor failed to enable.\n");
                return 1;
            }
            usleep(1000);
        }

        // 3. Homing Sequence 
        // Motor uses settings (including Offset) saved in its Flash via ClearView
        if (!g_node->Motion.Homing.HomingValid()) {
            printf("Error: Homing not configured/valid in motor flash.\n");
            return 1;
        }

        printf("Node found: %s. Initiating Homing Sequence...\n", g_node->Info.UserID.Value());
        g_node->Motion.Homing.Initiate();

        // The motor will hit the hardstop and then move to its offset automatically.
        // WasHomed() only turns true AFTER the offset move is complete.
        double homingTimeout = g_mgr->TimeStampMsec() + timeout_ms;
        while (!g_node->Motion.Homing.WasHomed()) {
            g_node->Status.RT.Refresh();
            if (g_node->Status.RT.Value().cpm.AlertPresent || g_mgr->TimeStampMsec() > homingTimeout) {
                printf("Homing failed: Alert triggered or Timeout reached.\n");
                g_node->EnableReq(false);
                return 1;
            }
            usleep(1000);
        }

        // 4. Force Position to Zero and Signal Complete
        // Refresh the position after the hardware move to the offset is done
        g_node->Motion.PosnMeasured.Refresh();
        
        // Take the current internal count and subtract it from itself
        // to force the motor's internal register to exactly 0.
        double currentPos = g_node->Motion.PosnMeasured.Value();
        g_node->Motion.AddToPosition(-currentPos); 
        
        // Now signal that homing is complete at this new 0 point
        g_node->Motion.Homing.SignalComplete();

        printf("Setup and Homing complete. Position forced to 0 (Offset applied).\n");
        return 0;

    } catch (mnErr& e) {
        printf("Setup/Homing Error: %s\n", e.ErrorMsg);
        return 1;
    } catch (...) {
        printf("Unknown error during setup/homing.\n");
        return 1;
    }
}

// Exported: set acceleration and velocity limits
extern "C" int acceleration_velocity_set(int acceleration, int velocity) {
    if (!g_node) {
        printf("Node not initialized. Call setup() first.\n");
        return 1;
    }

    g_node->AccUnit(INode::RPM_PER_SEC);
    g_node->VelUnit(INode::RPM);
    g_node->Motion.AccLimit = acceleration;
    g_node->Motion.VelLimit = velocity;

    printf("Set AccLimit=%d rpm/s, VelLimit=%d rpm\n", acceleration, velocity);
    return 0;
}

// Exported: Move at specified velocity
extern "C" int move_speed(int target) {
    if (!g_node) {
        // Updated to match your new combined function name
        printf("Node not initialized. Call setup_and_home() first.\n");
        return 1;
    }
    
    bool ok = moveAtVelocity(*g_node, target);
    return ok ? 0 : 1;
}

// Exported: perform a move
extern "C" int move_counts(int target, int isAbsolute) {
    if (!g_node) {
        printf("Node not initialized. Call setup() first.\n");
        return 1;
    }

    bool ok = moveDistance(*g_node, target, isAbsolute != 0);
    return ok ? 0 : 1;
}

// Exported: shutdown
extern "C" void shutdown_node() {
    if (g_node) {
        g_node->EnableReq(false);
    }
    if (g_mgr) {
        g_mgr->PortsClose();
    }
}

// --- helpers from your original code ---

void msgUser(const char* msg) {
    std::cout << msg;
    getchar();
}

void printNodeInfo(INode& node) {
    printf("   Node[%d]: type=%d\n", node.Info.Ex.NodeIndex(), node.Info.NodeType());
    printf("            userID: %s\n", node.Info.UserID.Value());
    printf("        FW version: %s\n", node.Info.FirmwareVersion.Value());
    printf("          Serial #: %d\n", node.Info.SerialNumber.Value());
    printf("             Model: %s\n", node.Info.Model.Value());
}

bool moveDistance(INode& node, int target, bool targetIsAbsolute) {
    if (!node.Motion.IsReady()) {
        printf("Node[%d]: Move cancelled; node not ready\n", node.Info.Ex.NodeIndex());
        return false;
    }

    node.Status.Rise.Refresh();
    node.Status.Rise.Clear();

    printf("Node[%d]: Moving %d counts, isAbsolute=%d\n",
           node.Info.Ex.NodeIndex(), target, targetIsAbsolute);
    node.Motion.MovePosnStart(target, targetIsAbsolute);
    double est = node.Motion.MovePosnDurationMsec(target, targetIsAbsolute);
    printf("%.2f ms estimated.\n", est);

    while (!node.Motion.MoveIsDone());

    mnStatusReg mask;
    mask.cpm.AlertPresent = 1;
    mask.cpm.MoveCanceled = 1;

    mnStatusReg result;
    if (node.Status.Rise.TestAndClear(mask, result)) {
        if (result.cpm.AlertPresent)
            printf("Move failed: AlertPresent\n");
        if (result.cpm.MoveCanceled)
            printf("Move failed: MoveCanceled\n");
        return false;
    }

    printf("Node[%d]: Move Done\n", node.Info.Ex.NodeIndex());
    return true;
}

bool moveAtVelocity(INode& node, int target) {
    if (!node.Motion.IsReady()) {
        printf("Node[%d]: Move canceled. Node not ready.\n", node.Info.Ex.NodeIndex());
        return false;
    }

    node.Status.Rise.Refresh();
    node.Status.Rise.Clear();

    printf("Node[%d]: Ramping to velocity %d RPM...\n", node.Info.Ex.NodeIndex(), target);
    node.Motion.MoveVelStart(target);

    // Set a safety timeout (e.g., 5 seconds to reach target speed)
    double timeoutTime = g_mgr->TimeStampMsec() + 5000;

    // Wait for target velocity
    while (!node.Motion.VelocityAtTarget()) {
        if (g_mgr->TimeStampMsec() > timeoutTime) {
            printf("Node[%d]: Error - Failed to reach target velocity (Timeout).\n", node.Info.Ex.NodeIndex());
            node.Motion.NodeStop(STOP_TYPE_ABRUPT);
            return false;
        }
        usleep(1000); // Prevent 100% CPU usage
    }

    // Check for alerts during the ramp-up
    mnStatusReg mask;
    mask.cpm.AlertPresent = 1;
    mask.cpm.MoveCanceled = 1;
    mnStatusReg result;
    
    node.Status.Rise.Refresh();
    if (node.Status.Rise.TestAndClear(mask, result)) {
        if (result.cpm.AlertPresent) printf("Node[%d]: Alert during velocity ramp.\n", node.Info.Ex.NodeIndex());
        return false;
    }
    
    printf("Node[%d]: Target Velocity Reached.\n", node.Info.Ex.NodeIndex());
    return true;
}

//bool moveAtVelocity(INode& node, int target) {
	//// we can't execute a move unless the node is ready to recieve motion commands
	//if (!node.Motion.IsReady()) {
		//printf("Node[%d]: Move canceled because the Node is not ready\n", node.Info.Ex.NodeIndex());
		//printf("Make sure to clear Alerts and NodeStops and ensure the node is Enabled.\n");
		//return false;
	//}

	//// Refresh then Clear the rising register before starting the move so that
	//// we can detect events that occured during the move.
	//node.Status.Rise.Refresh();
	//node.Status.Rise.Clear();

	//printf("Node[%d]: Ramping to velocity %d\n", node.Info.Ex.NodeIndex(), target);
	//node.Motion.MoveVelStart(target); //Execute velocity move

	//// Wait for the node to reach it's target velocity
	//// Note: MoveDone is asserted when a move completes successfully or when the node has a shutdown.
	//while (!node.Motion.VelocityAtTarget());

	//mnStatusReg mask; // Create a status register mask to test the Rising register
	//mask.cpm.AlertPresent = 1; // set AlertPresent
	//mask.cpm.MoveCanceled = 1; // set MoveCanceled

	//mnStatusReg result; // store results from test
	//// Verify the motor didn't go into alert during the move
	//// and that the move wasn't cancelled
	//if (node.Status.Rise.TestAndClear(mask, result)) {
		//if (result.cpm.AlertPresent) {
			//printf("Node[%d]: Move failed due to AlertPresent\n", node.Info.Ex.NodeIndex());
		//}
		//if (result.cpm.MoveCanceled) {
			//printf("Node[%d]: Move failed due to MoveCanceled\n", node.Info.Ex.NodeIndex());
		//}
		//return false; // move did not complete successfully
	//}
	
	//printf("Node[%d]: Velocity Reached\n", node.Info.Ex.NodeIndex());
	//return true;
//}
