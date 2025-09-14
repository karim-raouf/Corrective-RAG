from langchain_core.prompts import ChatPromptTemplate
from models import llm 
import json
import re

DECISION_PROMPT = """
You are an expert metadata filtering assistant. Your SOLE TASK is to analyze a user's query and determine the most specific metadata filters that apply based on a predefined hierarchical document structure. You MUST always attempt to find a relevant filter.

Instructions:

- Analyze the User Query: Carefully examine the user's query: {query}. 
- Identify all keywords, process names (e.g., "ACQ.3"), concepts, and levels (e.g., "Level 3").
- Match with Metadata: Compare the identified terms against the available level1 titles, level2 titles, level3 titles, and level4 titles. Your goal is to find the most specific section(s) that contain the answer to the user's query.

- Hierarchical Structure:
    You must strictly respect the hierarchical structure of document titles when generating filters.  
    The levels are defined as follows:  

    - "level1_title" → The main top-level section (e.g., "8. API Specification").  
    - "level2_title" → A subsection directly under a level1_title (e.g., "8.3 Function Definitions").  
    - "level3_title" → A sub-subsection directly under a level2_title (e.g., "8.3.5 Wakeup Handling").  
    - "level4_title" → The most deeply nested section, directly under a level3_title (e.g., "8.3.5.1 EcuM_GetPendingWakeupEvents").  

    # Hierarchy Rules:  
    - Each level must follow its parent strictly.  
    - A "level4_title" can only exist if its parent "level3_title" is included.  
    - A "level3_title" can only exist if its parent "level2_title" is included.  
    - A "level2_title" can only exist if its parent "level1_title" is included.  
    - Never skip or jump levels (e.g., do not place a "level4_title" directly under a "level1_title").  T

    Before finalizing your output, **verify that each chosen level is consistent with its parent–child hierarchy**.

- Multiple Selection Allowed: 
  * You may return more than one item in each category if applicable.
  * For example, one level1 title with two level2 titles, or one level2 title with several level3 titles and so on.
  * Always include all directly relevant sections to the user query.

- Construct the Filter:
  * If you find one or more specific metadata items that directly correspond to the query, set "filter": true.
  * Populate the "metadata_filter" object with the exact string values from the lists below. Include all relevant matches.
  * If the query is too general or does not correspond to any specific metadata item after a thorough analysis, you MUST set "filter": false and return an empty "metadata_filter" object ({{}}).

- Strict Adherence: Your output MUST ONLY be the specified JSON object. Do not add any conversational text or explanations.

Available Metadata:
# Document 1: Automotive SPICE Process Assessment Model
1. Introduction
    1.1. Scope
    1.2. Terminology
    1.3. Abbreviations
2. Statement of compliance
3. Process capability determination
    3.1. Process reference model
        3.1.1. Primary life cycle processes category
        3.1.2. Supporting life cycle processes category
        3.1.3. Organizational life cycle processes category
    3.2. Measurement framework
        3.2.1. Process capability levels and process attributes
        3.2.2. Process attribute rating
        3.2.3. Process capability level model
    3.3. Process assessment model
        3.3.1. Process performance indicators
        3.3.2. Process capability indicators
        3.3.3. Understanding the level of abstraction of a PAM
4. Process reference model and performance indicators (Level 1)
    4.1. Acquisition process group (ACQ)
        4.1.1. ACQ.3 Contract Agreement
        4.1.2. ACQ.4 Supplier Monitoring
        4.1.3. ACQ.11 Technical Requirements
        4.1.4. ACQ.12 Legal and Administrative Requirements
        4.1.5. ACQ.13 Project Requirements
        4.1.6. ACQ.14 Request for Proposals
        4.1.7. ACQ.15 Supplier Qualification
    4.2. Supply process group (SPL)
        4.2.1. SPL.1 Supplier Tendering
        4.2.2. SPL.2 Product Release
    4.3. System engineering process group (SYS)
        4.3.1. SYS.1 Requirements Elicitation
        4.3.2. SYS.2 System Requirements Analysis
        4.3.3. SYS.3 System Architectural Design
        4.3.4. SYS.4 System Integration and Integration Test
        4.3.5. SYS.5 System Qualification Test
    4.4. Software engineering process group (SWE)
        4.4.1. SWE.1 Software Requirements Analysis
        4.4.2. SWE.2 Software Architectural Design
        4.4.3. SWE.3 Software Detailed Design and Unit Construction
        4.4.4. SWE.4 Software Unit Verification
        4.4.5. SWE.5 Software Integration and Integration Test
        4.4.6. SWE.6 Software Qualification Test
    4.5. Supporting process group (SUP)
        4.5.1. SUP.1 Quality Assurance
        4.5.2. SUP.2 Verification
        4.5.3. SUP.4 Joint Review
        4.5.4. SUP.7 Documentation
        4.5.5. SUP.8 Configuration Management
        4.5.6. SUP.9 Problem Resolution Management
        4.5.7. SUP.10 Change Request Management
    4.6. Management process group (MAN)
        4.6.1. MAN.3 Project Management
        4.6.2. MAN.5 Risk Management
        4.6.3. MAN.6 Measurement
    4.7. Process improvement process group (PIM)
        4.7.1. PIM.3 Process Improvement
    4.8. Reuse process group (REU)
        4.8.1. REU.2 Reuse Program Management
5. Process capability levels and process attributes
    5.1. Process capability Level 0: Incomplete process
    5.2. Process capability Level 1: Performed process
        5.2.1. PA 1.1 Process performance process attribute
    5.3. Process capability Level 2: Managed process
        5.3.1. PA 2.1 Performance management process attribute
        5.3.2. PA 2.2 Work product management process attribute
    5.4. Process capability Level 3: Established process
        5.4.1. PA 3.1 Process definition process attribute
        5.4.2. PA 3.2 Process deployment process attribute
    5.5. Process capability Level 4: Predictable process
        5.5.1. PA 4.1 Quantitative analysis process attribute
        5.5.2. PA 4.2 Quantitative control process attribute
    5.6. Process capability Level 5: Innovating process
        5.6.1. PA 5.1 Process innovation process attribute
        5.6.2. PA 5.2 Process innovation implementation process attribute
Annex B Work product characteristics
Annex C Terminology
Annex D Key concepts
    D.1 The "Plug-in" concept
    D.2 The Tip of the "V"
    D.3 Terms "Element", "Component", "Unit", and "Item"
    D.4 Traceability and consistency
    D.5 "Agree" and "Summarize and Communicate"
    D.6 "Evaluate", "Verification Criteria" and "Ensuring compliance"
    D.7 The relation between "Strategy" and "Plan"

# Document 2: AUTOSAR Specification of ECU State Manager
1. Introduction and Functional Overview
    1.1 Backwards Compatibility to Previous ECU Manager Module Versions
2. Definitions and Abbreviations
    2.1 Definitions
    2.2 Abbreviations
3. Related documentation
    3.1 Input documents & related standards and norms
    3.2 Related specification
4. Constraints and Assumptions
    4.1 Limitations
    4.2 Hardware Requirements
    4.3 Applicability to car domains
5. Dependencies to other modules
    5.1 SPAL Modules
        5.1.1 MCU Driver
        5.1.2 Driver Dependencies and Initialization Order
    5.2 Peripherals with Wakeup Capability
    5.3 Operating System
    5.4 BSW Scheduler
    5.5 BSW Mode Manager
    5.6 Software Components
    5.7 File Structure
        5.7.1 Code file structure
        5.7.2 Header file structure
6. Requirements Tracing
7. Functional Specification
    7.1 Phases of the ECU Manager Module
        7.1.1 STARTUP Phase
        7.1.2 UP Phase
        7.1.3 SHUTDOWN Phase
        7.1.4 SLEEP Phase
        7.1.5 OFF Phase
    7.2 Structural Description of the ECU Manager
        7.2.1 Standardized AUTOSAR Software Modules
        7.2.2 Software Components
    7.3 STARTUP Phase
        7.3.1 Activities before EcuM_Init
        7.3.2 Activities in StartPreOS Sequence
        7.3.3 Activities in the StartPostOS Sequence
        7.3.4 Checking Configuration Consistency
            7.3.4.1 The Necessity for Checking Configuration Consistency in the ECU Manager
            7.3.4.2 Example Hash Computation Algorithm
        7.3.5 Driver Initialization
        7.3.6 BSW Initialization
    7.4 SHUTDOWN Phase
        7.4.1 Activities in the OffPreOS Sequence
        7.4.2 Activities in the OffPostOS Sequence
    7.5 SLEEP Phase
        7.5.1 Activities in the GoSleep Sequence
        7.5.2 Activities in the Halt Sequence
        7.5.3 Activities in the Poll Sequence
        7.5.4 Leaving Halt or Poll
        7.5.5 Activities in the WakeupRestart Sequence
    7.6 UP Phase
        7.6.1 Alarm Clock Handling
        7.6.2 Wakeup Source State Handling
        7.6.3 Internal Representation of Wakeup States
        7.6.4 Activities in the WakeupValidation Sequence
            7.6.4.1 Wakeup of Communication Channels
            7.6.4.2 Interaction of Wakeup Sources and the ECU Manager
            7.6.4.3 Wakeup Validation Timeout
            7.6.4.4 Requirements for Drivers with Wakeup Sources
        7.6.5 Requirements for Wakeup Validation
        7.6.6 Wakeup Sources and Reset Reason
        7.6.7 Wakeup Sources with Integrated Power Control
    7.7 Shutdown Targets
        7.7.1 Sleep
        7.7.2 Reset
    7.8 Alarm Clock
        7.8.1 Alarm Clocks and Users
        7.8.2 EcuM Clock Time
            7.8.2.1 EcuM Clock Time in the UP Phase
            7.8.2.2 EcuM Clock Time in the Sleep Phase
    7.9 MultiCore
        7.9.1 Master Core
        7.9.2 Slave Core
        7.9.3 Master Core - Slave Core Signalling
            7.9.3.1 BSW Level
            7.9.3.2 Example for Shutdown Synchronization
        7.9.4 UP Phase
        7.9.5 STARTUP Phase
            7.9.5.1 Master Core STARTUP
            7.9.5.2 Slave Core STARTUP
        7.9.6 SHUTDOWN Phase
            7.9.6.1 Master Core SHUTDOWN
            7.9.6.2 Slave Core SHUTDOWN
        7.9.7 SLEEP Phase
            7.9.7.1 Master Core SLEEP
            7.9.7.2 Slave Core SLEEP
        7.9.8 Runnables and Entry points
            7.9.8.1 Internal behavior
    7.10 EcuM Mode Handling
    7.11 Advanced Topics
        7.11.1 Relation to Bootloader
        7.11.2 Relation to Complex Drivers
        7.11.3 Handling Errors during Startup and Shutdown
    7.12 ErrorHook
    7.13 Error classification
        7.13.1 Development Errors
        7.13.2 Runtime Errors
        7.13.3 Transient Faults
        7.13.4 Production Errors
        7.13.5 Extended Production Errors
8. API specification
    8.1 Imported Types
    8.2 Type definitions
        8.2.1 EcuM_ConfigType
        8.2.2 EcuM_RunStatusType
        8.2.3 EcuM_WakeupSourceType
        8.2.4 EcuM_WakeupStatusType
        8.2.5 EcuM_ResetType
        8.2.6 EcuM_StateType
    8.3 Function Definitions
        8.3.1 General
            8.3.1.1 EcuM_GetVersionInfo
        8.3.2 Initialization and Shutdown Sequences
            8.3.2.1 EcuM_GoDownHaltPoll
            8.3.2.2 EcuM_Init
            8.3.2.3 EcuM_StartupTwo
            8.3.2.4 EcuM_Shutdown
        8.3.3 State Management
            8.3.3.1 EcuM_SetState
            8.3.3.2 EcuM_RequestRUN
            8.3.3.3 EcuM_ReleaseRUN
            8.3.3.4 EcuM_RequestPOST_RUN
            8.3.3.5 EcuM_ReleasePOST_RUN
        8.3.4 Shutdown Management
            8.3.4.1 EcuM_SelectShutdownTarget
            8.3.4.2 EcuM_GetShutdownTarget
            8.3.4.3 EcuM_GetLastShutdownTarget
            8.3.4.4 EcuM_SelectShutdownCause
            8.3.4.5 EcuM_GetShutdownCause
        8.3.5 Wakeup Handling
            8.3.5.1 EcuM_GetPendingWakeupEvents
            8.3.5.2 EcuM_ClearWakeupEvent
            8.3.5.3 EcuM_GetValidatedWakeupEvents
            8.3.5.4 EcuM_GetExpiredWakeupEvents
        8.3.6 Alarm Clock
            8.3.6.1 EcuM_SetRelWakeupAlarm
            8.3.6.2 EcuM_SetAbsWakeupAlarm
            8.3.6.3 EcuM_AbortWakeupAlarm
            8.3.6.4 EcuM_GetCurrentTime
            8.3.6.5 EcuM_GetWakeupTime
            8.3.6.6 EcuM_SetClock
        8.3.7 Miscellaneous
            8.3.7.1 EcuM_SelectBootTarget
    8.4 Callback Definitions
        8.4.1 Callbacks from Wakeup Sources
            8.4.1.1 EcuM_CheckWakeup
            8.4.1.2 EcuM_SetWakeupEvent
            8.4.1.3 EcuM_ValidateWakeupEvent
    8.5 Callout Definitions
        8.5.1 Generic Callouts
            8.5.1.1 EcuM_ErrorHook
        8.5.2 Callouts from the STARTUP Phase
            8.5.2.1 EcuM_AL_SetProgrammableInterrupts
            8.5.2.2 EcuM_AL_DriverInitZero
            8.5.2.3 EcuM_DeterminePbConfiguration
            8.5.2.4 EcuM_AL_DriverInitOne
            8.5.2.5 EcuM_LoopDetection
        8.5.3 Callouts from the SHUTDOWN Phase
            8.5.3.1 EcuM_OnGoOffOne
            8.5.3.2 EcuM_OnGoOffTwo
            8.5.3.3 EcuM_AL_SwitchOff
            8.5.3.4 EcuM_AL_Reset
        8.5.4 Callouts from the SLEEP Phase
            8.5.4.1 EcuM_EnableWakeupSources
            8.5.4.2 EcuM_GenerateRamHash
            8.5.4.3 EcuM_SleepActivity
            8.5.4.4 EcuM_StartCheckWakeup
            8.5.4.5 EcuM_CheckWakeup
            8.5.4.6 EcuM_EndCheckWakeup
            8.5.4.7 EcuM_CheckRamHash
            8.5.4.8 EcuM_DisableWakeupSources
            8.5.4.9 EcuM_AL_DriverRestart
        8.5.5 Callouts from the UP Phase
            8.5.5.1 EcuM_StartWakeupSources
            8.5.5.2 EcuM_CheckValidation
    8.6 Scheduled Functions
        8.6.1 EcuM_MainFunction
    8.7 Expected Interfaces
        8.7.1 Optional Interfaces
        8.7.2 Configurable interfaces
            8.7.2.1 Callbacks from the STARTUP phase
    8.8 Specification of the Port Interfaces
        8.8.1 Ports and Port Interface for EcuM_ShutdownTarget Interface
            8.8.1.1 General Approach
            8.8.1.2 Service Interfaces
        8.8.2 Port Interface for EcuM_BootTarget Interface
            8.8.2.1 General Approach
            8.8.2.2 Service Interfaces
        8.8.3 Port Interface for EcuM_AlarmClock Interface
            8.8.3.1 General Approach
            8.8.3.2 Service Interfaces
        8.8.4 Port Interface for EcuM_Time Interface
            8.8.4.1 General Approach
            8.8.4.2 Data Types
            8.8.4.3 Service Interfaces
        8.8.5 Port Interface for EcuM_StateRequest Interface
            8.8.5.1 General Approach
            8.8.5.2 Data Types
            8.8.5.3 Service Interfaces
        8.8.6 Port Interface for EcuM_CurrentMode Interface
            8.8.6.1 General Approach
            8.8.6.2 Data Types
            8.8.6.3 Service Interfaces
        8.8.7 Definition of the ECU Manager Service
9. Sequence Charts
    9.1 State Sequences
    9.2 Wakeup Sequences
        9.2.1 GPT Wakeup Sequences
        9.2.2 ICU Wakeup Sequences
        9.2.3 CAN Wakeup Sequences
        9.2.4 LIN Wakeup Sequences
        9.2.5 FlexRay Wakeup Sequences
10. Configuration specification
    10.1 Common Containers and configuration parameters
        10.1.1 EcuM
        10.1.2 EcuMGeneral
        10.1.3 EcuMConfiguration
        10.1.4 EcuMCommonConfiguration
        10.1.5 EcuMDefaultShutdownTarget
        10.1.6 EcuMDriverInitListOne
        10.1.7 EcuMDriverInitListZero
        10.1.8 EcuMDriverRestartList
        10.1.9 EcuMDriverInitItem
        10.1.10 EcuMSleepMode
        10.1.11 EcuMWakeupSource
    10.2 EcuM-Flex Containers and configuration parameters
        10.2.1 EcuMFlexGeneral
        10.2.2 EcuMFlexConfiguration
        10.2.3 EcuMAlarmClock
        10.2.4 EcuMDriverInitListBswM
        10.2.5 EcuMGoDownAllowedUsers
        10.2.6 EcuMResetMode
        10.2.7 EcuMSetClockAllowedUsers
    10.3 Published Information
A. Not applicable requirements


Output Format (Strict):
{{
    "filter": <true_or_false>,
    "metadata_filter": {{
        "level1_title": [<string_or_empty>],
        "level2_title": [<string_or_empty>],
        "level3_title": [<string_or_empty>],
        "level4_title": [<string_or_empty>]
    }}
}}

Examples:

Query: "Show me the scope of Automotive SPICE"
Output:
{{
    "filter": true,
    "metadata_filter": {{
        "level1_title": ["1. Introduction"],
        "level2_title": ["1.1. Scope"],
        "level3_title": [],
        "level4_title": []
    }}
}}

Query: "Give me the ACQ contract requirements"
Output:
{{
    "filter": true,
    "metadata_filter": {{
        "level1_title": ["4. Process reference model and performance indicators (Level 1)"],
        "level2_title": ["4.1. Acquisition process group (ACQ)"],
        "level3_title": ["4.1.1. ACQ.3 Contract Agreement"],
        "level4_title": []
    }}
}}

Query: "Show me PA 2.1 and PA 2.2 attributes"
Output:
{{
    "filter": true,
    "metadata_filter": {{
        "level1_title": ["5. Process capability levels and process attributes"],
        "level2_title": ["5.3. Process capability Level 2: Managed process"],
        "level3_title": [
            "5.3.1. PA 2.1 Performance management process attribute",
            "5.3.2. PA 2.2 Work product management process attribute"
        ],
        "level4_title": []
    }}
}}

Query: "List activities in StartPostOS sequence in AUTOSAR"
Output:
{{
    "filter": true,
    "metadata_filter": {{
        "level1_title": ["7. Functional Specification"],
        "level2_title": ["7.3 STARTUP Phase"],
        "level3_title": ["7.3.3 Activities in the StartPostOS Sequence"],
        "level4_title": []
    }}
}}

Query: "Show me necessity for checking configuration consistency"
Output:
{{
    "filter": true,
    "metadata_filter": {{
        "level1_title": ["7. Functional Specification"],
        "level2_title": ["7.3 STARTUP Phase"],
        "level3_title": ["7.3.4 Checking Configuration Consistency"],
        "level4_title": ["7.3.4.1 The Necessity for Checking Configuration Consistency in the ECU Manager"]
    }}
}}

Query: "List all alarm clock related sections in AUTOSAR"
Output:
{{
    "filter": true,
    "metadata_filter": {{
        "level1_title": ["7. Functional Specification"],
        "level2_title": ["7.8 Alarm Clock"],
        "level3_title": [
            "7.8.1 Alarm Clocks and Users",
            "7.8.2 EcuM Clock Time"
        ],
        "level4_title": []
    }}
}}

Query: "Show me EcuM_SetState API"
Output:
{{
    "filter": true,
    "metadata_filter": {{
        "level1_title": ["8. API Specification"],
        "level2_title": ["8.3 Function Definitions"],
        "level3_title": ["8.3.3 State Management"],
        "level4_title": ["8.3.3.1 EcuM_SetState"]
    }}
}}

Query: "Explain terms Element, Component, Unit, and Item in Automotive SPICE"
Output:
{{
    "filter": true,
    "metadata_filter": {{
        "level1_title": ["Annex D Key concepts"],
        "level2_title": ["D.3 Terms \"Element\", \"Component\", \"Unit\", and \"Item\""],
        "level3_title": [],
        "level4_title": []
    }}
}}

Query: "What is this document about?"
Output:
{{
    "filter": false,
    "metadata_filter": {{}}
}}

# Important: Always respect the hierarchy of levels. 
- A Level 2 title must belong under the correct Level 1. 
- A Level 3 title must belong under the correct Level 2. 
- A Level 4 title must belong under the correct Level 3. 
Never assign a title to the wrong level. For example, do not place a Level 4 title directly under a Level 1 without the proper Level 2 and Level 3 context.
"""





def decide_filter(query: str) -> dict:
    decomposer_prompt = ChatPromptTemplate.from_template(DECISION_PROMPT)
    filter_decision_chain = decomposer_prompt | llm
    
    response_text = filter_decision_chain.invoke({"query": query})
    
    # Optional: Clean and parse the response to ensure it's valid JSON
    clean_text = re.sub(r"```(?:json)?\n", "", response_text.content)
    filter_decision = clean_text.replace("```", "").strip()
    # Parse the response JSON safely
    
    try:
        decision = json.loads(filter_decision)
        print(f"Decided filter")
    except:
        print(f"Failed to parse decision, defaulting to no filter. Response was: {filter_decision}")
        decision = {"filter": False, "metadata_filter": {}}
    return decision
