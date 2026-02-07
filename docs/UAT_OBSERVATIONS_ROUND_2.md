# Observations from UAT - Round 2

These are some of the observations that I've gathered during UAT.  I would like to have a plan put together to review and address each of these observations.

### Import Wizard
- I still notice a lot of numbers and low quality matches/suggestions showing up in suggested/extracted Payees during Import Wizard.  I think this could be better rectified by making the first step (after the "step 0" well known company matches) would be to do some of the following in this order:
  - replace ALL numbers (0-9) with a null character (i.e. remove numbers).
  - replace ALL hyphens with a space.
  - instead of trying to remove prefixes for merchants like Square and Toast (i.e. "SQ *" and "TST*"), note that there are now many, many merchants that use a alpha string followed by an asterisk.  So, just remove any prefix that is 5 or less characters followed by an asterisk.  That should take care of most of those.
- Also on the Import Wizard, I think it would be a good idea to set the Category for suggested Payees when creating/suggesting new Payees, and also setting the Category for Transactions being imported because I've noticed that Category isn't being setup. I think transaction category could maybe use the same Category as the Payee default category?
  