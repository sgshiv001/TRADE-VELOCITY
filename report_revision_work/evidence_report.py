from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.shared import Pt


root = Path(__file__).resolve().parents[1]
submission = root / "submission_files"
source = submission / "TradeVelocity_Project_Report_Updated_25Nov.docx"
result = submission / "TradeVelocity_Project_Report_Submission.docx"
doc = Document(source)
paragraphs = doc.paragraphs

edits = {
    31: "TradeVelocity is a stock exchange simulator for our Advanced Data Structures and Algorithms project. Each practice workspace has an order book for every symbol a trader uses. The problem is to select the right order to fill and keep the remaining quantities correct as traders place, amend, and cancel orders.",
    32: "When orders share a price, the engine must fill the earlier order first.",
    33: "After a partial fill, the remaining shares must stay at the same price and keep their place in the queue.",
    34: "When the final order at a price is cancelled, that price must disappear from the book.",
    35: "We compared two designs for storing active prices. One finds the next price by scanning a list. The other keeps indexes for the best price and for ordered depth. We wanted to measure the cost of maintaining those indexes as the number of prices grows.",
    36: "The hosted browser app gives each account a saved practice workspace. The Windows build runs locally. Both simulate orders with no broker connection. The chart page uses dated market data, which is separate from the orders in the workspace.",
    44: "1. Use price and then arrival time to choose which order fills first.",
    45: "2. Show open quantities and trade records after an order is filled, amended, or cancelled.",
    46: "3. Compare an indexed book and a list book on identical command sequences.",
    47: "4. Provide a saved workspace on the web and a portable Windows build.",
    48: "5. Check engine results against a simpler reference after each command.",
    52: "We kept matching in the Python engine so the same rules apply in the browser and on Windows.",
    56: "The lowest ask has priority for a buy and the highest bid has priority for a sell. At the selected price, the engine takes the order at the front of the queue. An incoming limit order can accept a better price than its own limit. Each fill uses the price of the order already in the book.",
    57: "One engine test starts with sell orders for 50 and 70 shares at ₹100, then 30 at ₹101. A market buy for 200 fills the three orders in that order. The remaining 50 shares expire. This case checks both kinds of priority and what happens when the book runs out of shares (Ref. 7).",
    63: "1. Validate the incoming order and give it an arrival sequence.",
    64: "2. Read the best price on the other side. If the book is empty or the price is outside the limit, go to step 5.",
    65: "3. Take the first order at that price. Fill the smaller of the two open quantities at the resting price.",
    66: "4. Record the trade, subtract the fill from both orders, and remove the resting order if it is filled. Delete the level if its queue is empty. Go back to step 2 if the incoming order still has shares.",
    67: "5. Queue any remaining limit shares. A market order’s remaining shares expire.",
    71: "Figure 1. How the engine processes an incoming order.",
    81: "The order ticket and depth screen need different views of the same book. The ticket needs the best price. Depth needs several prices in order. The heap and AVL tree provide those two views.",
    83: "With P active price levels on one side, a current heap root gives the best price in expected O(1) time. Creating a level takes amortized expected O(log(P + 1)). Reading k depth levels takes O(log P + k) for a nonempty book. Updating the Fenwick tree when recording a trade takes amortized O(log(T + 1)) for T recorded trades.",
    84: "The deep-book test first placed 5,000 sell orders at distinct prices and then drained the book with 5,000 market buys. On Windows, median throughput was 73,122 commands per second for the indexed book and 5,495 for the list. The separate memory pass measured peaks of 5.28 MiB and 3.84 MiB, respectively. The mixed test also used 10,000 commands but had only eleven possible prices. There the list reached 134,663 commands per second versus 106,660 for the indexed design (Ref. 6).",
    85: "The 28 October verification records 160 Python tests, 13 browser checks and a passing packaged Windows smoke test (Ref. 8). In a focused rerun on 25 November, five cases passed, covering resting price, FIFO, partial fills, market remainder, recreated prices, and comparison with an independent book after each of 1,200 commands (Ref. 7).",
    89: "The first two captures show the balance and the trade record for one RELIANCE test. The third capture is from a separate watchdog session (Ref. 8).",
    93: "Figure 2. The overview shows one trade for three shares and one open sell order. Two of the original five sell shares remain.",
    96: "Figure 3. The history row shows RELIANCE, three shares, and a price of ₹100.",
    99: "Figure 4. The review queue shows the 5,000-share test execution after 40 baseline observations and six scored observations.",
    103: "Hash Syndicate developed one shared application. The project README records which area each member covered in the group presentation (Ref. 1).",
    107: "The tests below show three places where the design or the evaluation needed care.",
    109: "Cancelling the last order at ₹100 removes the price level, but the heap may still hold an entry for it. If ₹100 comes back, the generation token identifies the new level. The regression test creates and cancels that price 250 times on each side, then checks the next market order fills against the correct orders (Ref. 7).",
    110: "For the throughput test, we used the same matching loop in both versions. We compared trades, open orders, depth, and volume before timing. We also kept workload generation and memory tracing outside the timed section (Ref. 6).",
    111: "The watchdog sees one observation per order that produces fills. For each symbol it uses 24 observations to fit and 16 to set cutoffs. The separate alert shown in Figure 4 comes from a controlled test. The alert goes into a review queue and leaves the executed trade in place (Refs. 1 and 8).",
    114: "TradeVelocity demonstrates how price and arrival time turn an order into a trade and how that trade changes the book. The indexed design was faster in the deep test and took more memory. It made less sense when a list had only eleven possible prices to scan.",
    115: "Next, we would repeat the benchmark on another machine, run the portable Windows ZIP on a second physical PC, and add more time-in-force choices.",
    117: "The repository links below identify the source of the benchmark, the tests, and the screenshots.",
}
for index, wording in edits.items():
    paragraph = paragraphs[index]
    paragraph.clear().add_run(wording)

for table_index, row_index, column_index, description in (
    (1, 1, 2, "Takes the next compatible order and keeps track of filled and open shares."),
    (1, 2, 2, "Shows the best prices, open orders, and completed trades."),
    (1, 3, 2, "FastAPI passes orders to the engine. PostgreSQL saves hosted workspaces, and a session export can be replayed."),
    (1, 4, 2, "Shows dated market charts and gives unusual practice executions their own review queue."),
    (1, 5, 2, "Runs the same workload on both books. The portable Windows release includes the frontend and engine."),
    (2, 1, 1, "Keep the highest bid and lowest ask at the top of their respective heaps."),
    (2, 2, 1, "Return the requested price levels in order for the depth view."),
    (2, 3, 1, "Keep orders at one price in arrival order and support direct removal."),
    (2, 4, 1, "Map an ID to its queue node and a price to its level."),
    (2, 5, 1, "Answer how many shares traded within a range of trade IDs."),
    (2, 6, 1, "Append completed trades in increasing ID order."),
    (2, 7, 1, "Find a recorded trade by its ID in the sorted history."),
):
    paragraph = doc.tables[table_index].cell(row_index, column_index).paragraphs[0]
    run = paragraph.clear().add_run(description)
    run.font.name = "Calibri"
    run.font.size = Pt(10)

header = doc.tables[3].cell(0, 2).paragraphs[0]
header.runs[0].bold = True

def add_source(index, label, url):
    paragraph = paragraphs[124].insert_paragraph_before(
        f"{index}. ", style=paragraphs[123].style
    )
    paragraph.paragraph_format.left_indent = Pt(12)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.keep_together = True
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), paragraph.part.relate_to(
        url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True
    ))
    run = OxmlElement("w:r")
    properties = OxmlElement("w:rPr")
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    properties.append(underline)
    run.append(properties)
    content = OxmlElement("w:t")
    content.text = label
    run.append(content)
    link.append(run)
    paragraph._p.append(link)


repo = "https://github.com/sgshiv001/TRADE-VELOCITY/blob/main/"
add_source(6, "Benchmark workloads and archived measurements", repo + "docs/results.md")
add_source(7, "Correctness test cases and reference comparison", repo + "docs/evaluation.md")
add_source(8, "28 October verification and screenshot record",
           repo + "reports/project-check-2026-10-28/REPORT.md")

# Remove redundant briefings and blank spacing from the earlier version.
for index in (37, 38, 42, 58, 59, 60, 72, 73, 74, 75, 76, 77, 78, 86, 87, 112, 118):
    element = paragraphs[index]._p
    element.getparent().remove(element)

for index in (31, 56):
    paragraphs[index].paragraph_format.line_spacing = 1.25
for index in (57, 84, 85, 93, 96, 99, 109, 110, 111):
    paragraphs[index].paragraph_format.keep_together = True
for index in (70, 92, 95, 98):
    paragraphs[index].paragraph_format.keep_with_next = True
for index in (51, 69, 88, 116):
    paragraphs[index].paragraph_format.page_break_before = True

doc.save(result)
print(result)
