from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor

ROOT = Path(r'C:\Users\shivu\OneDrive\Documents\GitHub\ADSA PROJECT')
SOURCE = ROOT / 'submission_files' / 'TradeVelocity_Project_Report.docx'
OUTPUT = ROOT / 'submission_files' / 'TradeVelocity_Project_Report_Revised.docx'

doc = Document(SOURCE)

changes = {
    31: "We tested the matching rule with a sell of five shares at ₹100 and a buy of three. The engine should record a three-share trade and leave two shares on the sell side. This small case exposes the same issues as a larger book: best price, arrival order, and exact remaining quantities. Scanning an unsorted list is straightforward, but its cost grows as active price levels are added.",
    32: "The main problem was to keep the book correct while finding a compatible order quickly and recording exactly what traded.",
    33: "We built the workspace for classroom review: place orders, inspect depth, then compare the visible trade with the expected result.",
    34: "The benefit is visible evidence: the active orders, trade history, tests, and benchmark all refer to the same matching rules.",
    35: "TradeVelocity is a local simulation. It sends no orders to a broker or exchange. The dated market-history page is separate from the user-created order book, and choosing a symbol does not create counterparties.",
    36: "The engine handles each command; React and FastAPI display its state and save accepted commands for replay. We compared its indexed price book with an unsorted list book after checking that both reached the same trades and depth.",
    42: "We used the following targets to decide whether the project was complete:",
    44: "1. Match limit and market orders in price-time order, including partial fills at the resting order's price.",
    45: "2. Let a user amend or cancel an active order and then see the changed depth and full trade history.",
    46: "3. Use heaps, AVL trees, FIFO queues, hash tables, and a Fenwick tree where each one solves a specific lookup or update problem.",
    47: "4. Make the same local session usable from the browser and the portable Windows application.",
    48: "5. Check the trades against independent reference matchers before comparing performance with an unsorted list book.",
    52: "The application has five parts. The matching engine owns the order books; the other parts make its state visible, save it, monitor executions, and test its behaviour.",
    56: "Each stock symbol has its own buy and sell books. When an order arrives, the engine checks the best price on the opposite side. If that price is acceptable, it takes the oldest order at that level and trades the smaller of the two remaining quantities. The execution uses the resting order's price. After each fill, both quantities and the trade record are updated. The process repeats until the incoming order is filled or there is no compatible order left.",
    57: "The max heap exposes the highest bid, while the min heap exposes the lowest ask.",
    58: "An AVL tree keeps active prices ordered for the depth view.",
    59: "A FIFO queue at each price puts the earliest order at the front.",
    60: "Hash tables take us directly from an order ID or price to its active record.",
    63: "1. Check the symbol, side, type, quantity, price, and order ID; then assign the arrival sequence.",
    64: "2. Read the best opposite price. Stop if there is no liquidity or a limit order cannot accept that price.",
    65: "3. Trade the smaller remaining quantity against the oldest resting order. Record the resting price and update both orders.",
    66: "4. Remove an exhausted order or empty price level, then check whether another fill is possible.",
    67: "5. Put any unfilled limit quantity into the book. An unfilled market quantity expires.",
    81: "We chose each structure for a job that occurs repeatedly while an order is processed. The table shows what each structure contributes to the working book.",
    83: "Let P be the number of active prices on one side. With a current heap root, reading the best price is expected O(1). Adding a new level is amortized expected O(log(P + 1)), while reading k ordered depth levels is O(log P + k). A recorded trade also updates the Fenwick index, which is amortized O(log(T + 1)) after T trades. These are not worst-case promises for every command: hash collisions, resizing, and removal of stale heap entries can add work.",
    84: "We compared two price books under the same matching rules. Before timing, the harness checked their final trades and book state. In the archived deep-book run with 10,000 commands, the indexed version processed a median 73,122 commands per second; the unsorted list processed 5,495. The 13.31-times ratio came from that workload on one Windows machine. The mixed workload used only eleven prices. There the list processed 134,663 commands per second against 106,660 for the indexed version. Its short scans cost less than maintaining several indexes. We report both results because the shape of the book changes which design is faster.",
    85: "The correctness tests do more than count completed trades. They compare the engine with independent reference matchers, force hash collisions, check AVL balance, replay saved commands, and exercise cancellation after a price level disappears and returns. A test also checks that concurrent matches conserve shares. The repository records 160 passing Python tests on 1 November 2026. The separate 28 October check records 13 browser tests and a local Windows smoke test. These results describe our controlled environment, not exchange certification.",
    89: "These screenshots come from isolated application sessions used during verification. They show the book and history after real local commands, so the displayed quantities can be checked against the matching rule.",
    93: "Figure 2. A sell limit for five shares at ₹100 met a buy limit for three. The overview shows one trade and two sell shares still open.",
    96: "Figure 3. Trade History records the same three-share fill at ₹100.",
    99: "Figure 4. The watchdog flagged a controlled large execution for review; the alert did not change the match.",
    103: "Work was divided across matching, interface, backend, and validation. The repository README lists these focus areas, and the application was integrated as one shared codebase.",
    108: "Three parts needed particular care: keeping the book consistent after changes, comparing performance fairly, and explaining what the watchdog can actually conclude.",
    110: "Cancellation must remove an order from its FIFO queue and ID lookup, then delete the price level if it is empty. A heap entry can remain after deletion. The engine marks such entries with generation tokens so an old entry cannot revive a price level that was later created again. Cancellation-churn and reference-matcher tests exercise this case.",
    111: "The indexed and list books had to produce the same trades and final depth before we compared speed. The harness then timed the same commands three times per engine. Deep books favoured indexing; the mixed case, with only eleven prices, favoured a short list scan. We therefore report the workload and median rather than claim that one design always wins.",
    112: "The watchdog uses the first 40 executed-order observations per symbol: 24 fit the detector and 16 set cutoffs. It flags later price, size, or depth changes for review. An alert does not prove fraud or affect matching. Our controlled test injected synthetic deviations, so it does not measure real-market fraud accuracy.",
    115: "TradeVelocity now lets us follow a complete order from entry to execution and history. The example of five sell shares at ₹100 and a three-share buy leaves the expected two-share remainder, and the test suite checks much larger and less convenient cases. The indexed book helps when the number of active prices grows, as the deep-book benchmark shows. It also uses extra memory and maintenance work, which is why the short-price mixed workload favoured the list. The project remains a local teaching and testing application; it does not route orders to a real exchange.",
    116: "The next useful additions would be more time-in-force choices, benchmark runs on other machines, and a manual check of the portable Windows build on a second PC.",
    118: "The repository and the documentation below support the implementation details, test counts, and tools named in this report.",
}

for index, wording in changes.items():
    p = doc.paragraphs[index]
    p.clear()
    run = p.add_run(wording)
    run.font.color.rgb = RGBColor(0, 0, 0)

table_changes = {
    (1, 1, 2): "Checks the opposite book, matches the oldest order at the best compatible price, and records what remains after each fill.",
    (1, 2, 2): "Shows order entry, active orders, depth, and every trade generated in the local session.",
    (1, 3, 2): "FastAPI passes commands to the engine. Local storage keeps accepted commands, which are validated again during replay.",
    (1, 4, 2): "Keeps dated daily market history separate from the order book. The watchdog adds review alerts after executions.",
    (1, 5, 2): "Times identical commands on indexed and list books after checking their outcomes; packages the app for Windows.",
    (2, 1, 1): "The heap root gives the best buy or sell price. Generation tokens prevent stale entries from reviving an old level.",
    (2, 2, 1): "Maintain active prices in order, which supports the first k depth levels without sorting the whole book.",
    (2, 3, 1): "Keep orders in arrival order at one price. A cancellation unlinks its node directly.",
    (2, 4, 1): "Connect an order ID to its queue node and a price to its active level for expected fast lookup.",
    (2, 5, 1): "Update cumulative traded volume and answer prefix or range-volume questions.",
    (2, 6, 1): "Append completed trades in ID order as the session grows.",
    (2, 7, 1): "Locate a trade by its increasing ID without scanning the entire history.",
}
for (table_index, row, col), wording in table_changes.items():
    cell = doc.tables[table_index].cell(row, col)
    cell.text = wording
    for p in cell.paragraphs:
        p.paragraph_format.space_after = Pt(1)
        for run in p.runs:
            run.font.name = 'Calibri'
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0, 0, 0)

# Keep a screenshot caption on one page, and prevent the template's trailing
# declaration from becoming a page by itself.
doc.paragraphs[96].paragraph_format.keep_together = True
doc.paragraphs[110].paragraph_format.keep_together = True
for index in (34, 35):
    doc.paragraphs[index].paragraph_format.space_after = Pt(4)
doc.paragraphs[84].paragraph_format.space_after = Pt(8)
doc.paragraphs[103].paragraph_format.space_after = Pt(4)
for index in range(120, 125):
    doc.paragraphs[index].paragraph_format.space_after = Pt(2)
blank = doc.paragraphs[125]._element
blank.getparent().remove(blank)
extra = doc.paragraphs[104]._element
extra.getparent().remove(extra)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUTPUT)
print(OUTPUT)
print(f'Changed {len(changes)} paragraphs and {len(table_changes)} table cells')
