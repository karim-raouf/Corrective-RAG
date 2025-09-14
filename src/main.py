from CRAG_Graph import graph
# import sys
# import io

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
#What are the AUTOSAR Basic Software requirements [SRS_BSW] that the ECU Manager fulfills, and which remain unfulfilled?


question = """is software interface testing requested in SWE. 5?
            """

#List the base practices for MAN.3 Project Management process
output = graph.invoke({"question": question})
print("final answer: --------------------------------------------------")
print(output["final_output"])

