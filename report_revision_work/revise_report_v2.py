from pathlib import Path

from docx import Document
from docx.shared import RGBColor, Pt


root = Path(r"C:\Users\shivu\OneDrive\Documents\GitHub\ADSA PROJECT")
source = root / "submission_files" / "TradeVelocity_Project_Report_Revised.docx"
output = root / "submission_files" / "TradeVelocity_Project_Report_Updated_25Nov.docx"
document = Document(source)

# Keep the university template and the verified figures. Revise the text against
# the current repository README, architecture, evaluation, and hosted-workspace
# documentation. The indices refer to the 24 November revision.
replacements = {
    31: "An order book has to choose the next trade and leave the right quantity behind. In the example used here, a sell order for five shares at ₹100 meets a buy order for three. Three shares trade; two remain for sale. The result is simple to read on screen, but the engine still has to respect the best available price and the order in which requests arrived. We wanted to see how those rules behave as the book grows.",
    32: "Our main task was to keep fills correct after partial trades, amendments, and cancellations, while finding the next compatible order quickly.",
    33: "A reviewer can place orders, check the remaining depth, and find the resulting trade in the browser or Windows app.",
    34: "We checked those visible results against reference matchers and measured the price-book design separately.",
    35: "TradeVelocity is a practice exchange. The repository now links a hosted web app with separate saved workspaces for trader accounts, as well as a portable Windows build. No real money or shares move. The market-history screen shows dated daily data and does not supply orders to the practice book.",
    36: "The React interface sends a command to FastAPI, which calls the Python matching engine. Accepted commands can be replayed to rebuild a session. The hosted version stores accounts and workspaces in PostgreSQL; the Windows version keeps its own local session. Our performance comparison changes only the way the engine finds price levels.",
    42: "We used these objectives to guide the build and the checks:",
    44: "1. Match limit and market orders by price and arrival time, including partial fills at the resting order's price.",
    45: "2. Support amendment and cancellation, and show their effect in depth and trade history.",
    46: "3. Give each data structure a clear job in lookup, ordering, or trade-volume queries.",
    47: "4. Provide saved practice workspaces in the browser and a portable Windows version of the same application.",
    48: "5. Check correctness with independent matchers before timing the indexed and list-based price books.",
    52: "The matching engine processes orders. Around it, we built order-entry and history screens, session storage, a separate market-history view, and an execution watchdog. The Windows package runs the same frontend and engine locally.",
    56: "Every symbol has a buy book and a sell book. For an incoming buy, the engine looks at the lowest available sell price; for a sell, it looks at the highest buy price. A limit order trades only if that price meets its limit. At the chosen price, the oldest resting order goes first. The engine records a fill at that resting price, reduces both remaining quantities, and checks again. One incoming order can therefore create several trades. Any unfilled limit quantity stays in the book; an unfilled market remainder does not.",
    57: "The heaps expose the best buy and sell prices without scanning every level.",
    58: "The AVL trees keep price levels ordered when the interface asks for depth.",
    59: "The queue at a price level preserves arrival order among equal-priced orders.",
    60: "Hash tables locate an active order or price level directly for updates and cancellation.",
    63: "1. Validate the order fields and assign an arrival sequence.",
    64: "2. Look up the best price on the other side; stop when it is absent or outside the limit.",
    65: "3. Fill against the oldest order there, using its price and the smaller remaining quantity.",
    66: "4. Update the two orders and the trade record; remove exhausted orders and empty levels.",
    67: "5. Repeat while another fill is possible. Rest a limit remainder or expire a market remainder.",
    81: "The engine needs a quick answer to two different questions: what is the best price, and what are the next several prices in order? A heap handles the first question and an AVL tree handles the second. The other structures deal with orders inside a price level and with completed trades.",
    83: "Let P be the number of active prices on one side of the book. A valid heap root gives the best price in expected O(1) time. Creating a new level takes amortized expected O(log(P + 1)); reading k ordered depth levels takes O(log P + k). Recording a trade updates the Fenwick volume index in amortized O(log(T + 1)) time after T trades. A particular command can take longer when a hash table resizes or the heap discards old entries.",
    84: "Both versions in our benchmark use the same matching rules. The harness checked their trades and final book before timing them. With 10,000 commands in the deep-book workload, the indexed book handled a median 73,122 commands per second. The list version handled 5,495, so indexing was 13.31 times faster in that run. The result changed with a small price range: with only eleven possible prices, the list handled 134,663 commands per second and the indexed book 106,660. Scanning such a short list cost less than maintaining several indexes. These archived runs were made on one Windows machine, and the workload explains why their results differ.",
    85: "The archived local checks passed 160 Python tests on 1 November 2026. They cover price-time priority, partial fills, cancellation, replay, hash collisions, AVL balance, and conservation of shares under concurrent calls. The 28 October verification also passed 13 browser checks and a smoke test of the packaged Windows app. The README links a later, complete GitHub Actions run covering the frontend build, PostgreSQL, browser checks, and Python checks. None of these tests involve a real exchange.",
    89: "The first two images follow one controlled three-share trade from the overview to trade history. The third shows a review alert after a deliberately large execution. These are test-session screenshots, not live-market activity.",
    93: "Figure 2. Three of the five sell shares at ₹100 traded; the other two remain in the order book.",
    96: "Figure 3. Trade History shows the corresponding three-share execution at ₹100.",
    99: "Figure 4. A large test execution produced a watchdog alert while the match still completed.",
    103: "We developed and integrated TradeVelocity as a group. The README records the areas we divided for the presentation; the table follows that division.",
    107: "The trickiest case in the book was a price level that disappears and later returns. We also had to make sure the speed test compared like with like and that the watchdog was described within the limits of its evidence.",
    109: "When the last order at a price is cancelled, its queue node and lookup entry go away. The heap may still contain the old price because heap deletion is lazy. We use a generation token so that old entry cannot be mistaken for a new level created later at the same price. Repeated cancellation and recreation are part of the tests.",
    110: "A speed number would have meant little if the two books produced different trades. The harness first checked the entire outcome, then ran the same commands three times per engine. Indexing helped when the deep workload created thousands of price levels. With eleven prices, a short list scan won. The median and workload description are therefore both needed to understand the result.",
    111: "The watchdog looks only at completed executions. For each symbol, its first 24 observations fit the detector and the next 16 set cutoffs. Later changes in price, size, or depth can raise a review alert. The controlled test injected unusual activity, but an alert is not proof of fraud. The watchdog does not stop or change the matching decision.",
    114: "The app now lets us enter an order, watch the fill, and find the trade again in history. In the report's five-versus-three-share example, the two-share sell remainder is visible as expected. Independent tests cover less convenient cases, including cancellation and replay. The benchmark also gave us a useful correction: the indexed book paid off with many price levels, while a list was faster across only eleven prices. TradeVelocity remains a simulated practice exchange, even though the web version is hosted and the Windows build is portable.",
    115: "Useful next checks are a run of the portable Windows ZIP on another physical PC and benchmark runs on more machines. We would also like to add more time-in-force choices for orders.",
    117: "The project repository contains the code, measurement files, test reports, and design notes used here. The library documentation below covers the frameworks and algorithms we used.",
}

for index, wording in replacements.items():
    paragraph = document.paragraphs[index]
    paragraph.clear()
    run = paragraph.add_run(wording)
    run.font.color.rgb = RGBColor(0, 0, 0)

table = document.tables[1]
table_updates = {
    (1, 2): "Checks the opposite book and fills against the oldest order at the best compatible price.",
    (2, 2): "Lets a trader enter orders, inspect depth, amend or cancel, and revisit completed trades.",
    (3, 2): "FastAPI passes commands to the engine. The hosted app saves account workspaces in PostgreSQL; sessions can be exported and replayed.",
    (4, 2): "Shows dated market history separately from practice orders and flags unusual completed executions for review.",
    (5, 2): "Compares two price-book designs on checked workloads and packages the app for Windows.",
}
for (row, column), wording in table_updates.items():
    cell = table.cell(row, column)
    cell.text = wording
    for paragraph in cell.paragraphs:
        paragraph.paragraph_format.space_after = Pt(1)
        for run in paragraph.runs:
            run.font.name = "Calibri"
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0, 0, 0)

document.tables[3].cell(0, 2).text = "Area presented"

document.paragraphs[96].paragraph_format.keep_together = True
document.paragraphs[109].paragraph_format.keep_together = True
document.paragraphs[110].paragraph_format.keep_together = True
document.paragraphs[111].paragraph_format.keep_together = True

document.save(output)
print(output)
print(f"Revised {len(replacements)} paragraphs and {len(table_updates)} module descriptions")
