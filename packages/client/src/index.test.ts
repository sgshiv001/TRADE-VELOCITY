import { describe, expect, it } from "vitest";
import { limitOrderSchema } from "./index";

const order = {order_id: "sample", symbol: "m&m", side: "BUY", quantity: 2, price: "123.45", confirmed: true};
describe("confirmed paper limit order", () => {
  it("normalizes supported stock symbols and preserves the decimal price", () => {
    expect(limitOrderSchema.parse(order)).toMatchObject({symbol: "M&M", price: "123.45"});
  });
  it("rejects unconfirmed orders, fractional shares, and sub-paisa prices", () => {
    for (const override of [{confirmed: false}, {quantity: 2.5}, {price: "1.001"}]) {
      expect(limitOrderSchema.safeParse({...order, ...override}).success).toBe(false);
    }
  });
});
