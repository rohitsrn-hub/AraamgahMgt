# October 2026: why the app and the paper register differed, and what now prevents it

Reconciled on 19–20 Nov 2026 against the paper register (160 entries). After the
owner-approved corrections, October is ₹2,42,275 in all four reports. The register's
amount column totals ₹2,42,650. The ₹375 difference is fully explained and is not an error:

- **₹450 of extra beds on stays that checked out on 1 November** (BK1267 ₹150, BK1320 ₹150,
  BK1324 ₹75, BK1325 ₹75). The register puts the whole bill in the month the guest arrived; the
  app (owner ruling) counts a bed in the month of check-out, so these are in November's figures.
- **₹75 the other way on BK1031** (register serials 51–52): the register's amount column leaves
  out a ₹75 extra bed that its own balance includes. The app is right.

| What went wrong | Bookings | Root cause | What now stops it |
|---|---|---|---|
| A guest who never stayed was billed ₹21,000 | BK1293 | Checked in by mistake and left "checked in" for a month; the check-out screen defaulted to today, so 35 nights were billed | Red "still checked in past check-out date" reminder on Bookings; check-out opens at the booked date; a check-out 2+ nights late needs confirmation showing the extra rupees |
| Non-Org rate where staff charged Org (₹4,600) | BK1184, 1122, 0999, 0995, 1152, 1161, 1228, 1286, 1258 | At check-in the app bills a room Non-Org if any family member in it has no Org card; staff charge Org in practice | Check-in asks staff to confirm every Non-Org room and says why. **Owner to decide the rule itself** |
| Full-stay penalty the register did not charge (₹2,000) | BK1184, 1138 | Early departure not announced at check-in | Rule kept; an administrator can waive it at check-out (recorded with who and how much) |
| Extra beds collected but not entered | BK1280, 1151, 1204 | Bed not entered on the check-out screen; the higher payment was saved without question | Check-out now refuses a payment that differs from the bill unless staff confirm and give a reason |
| Advance taken but not entered, or entered wrong | BK1286 (₹800), BK1159 (₹500), BK1279 (₹800 entered, ₹400 taken) | Advance handled on paper only | Same payment check: the shortfall or excess is caught at check-out |
| Dashboard Net Revenue disagreed with the bookings | same three | The dashboard counts the payments log, a separate record from the booking's advance / final payment; corrections changed only the booking | Correction adds adjustment rows to the log; the Audit check now lists any booking whose log differs (`cash_log_differs`) |
| Room Occupancy report showed every guest as fully paid | all | Its "final paid" column was "bill minus advance", not the money recorded | Now shows the payment actually recorded |

## Toward paperless

The register has been the check on the app. Before dropping it, the app must catch what the
register caught: the payment check at check-out, the overdue reminder, and the monthly Audit
check (`cash_log_differs`, `under_collected`, `over_collected`) do that. Two things the owner
still needs to settle: the Non-Org rule at check-in, and how a stay's extra beds are split when
it crosses a month end (today: all in the check-out month).
