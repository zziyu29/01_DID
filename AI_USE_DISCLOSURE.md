# AI Use Disclosure

This disclosure documents how I used AI tools in this project, how I checked the AI-generated code, analysis, and writing, and which important AI errors or suggestions I corrected or rejected.

## 1. How AI was used: areas and methods

**Tools**: I used two AI tools — ChatGPT and Claude. AI was used mainly to help me understand the empirical methodology, write Python code, debug errors, interpret statistical results, and organize the project documentation. The detailed records below are based primarily on my actual interactions with ChatGPT and Claude.

**Specific areas of use**:

- **Understanding the original paper**: understanding the difference-in-differences (DID) method in Card and Krueger (1994), full-time-equivalent (FTE) employment, sample construction, and the regression models; identifying the variables needed for Table 2–4 and Figure 1, and understanding how the paper handled closed restaurants and wage differences.
- **Python code development**: constructing variables and replicating Table 2 (descriptive statistics), Figure 1 (wage distribution), Table 3 (employment levels and changes), and Table 4 (wage gap, sample selection, five OLS models); and organizing the output files and saving the processed data to improve reproducibility.
- **Debugging**: resolving Python library-installation, file-path, output-format, missing-variable, sample-selection-rule, and file-saving errors; by checking error messages and intermediate results, modifying the code, and rerunning the analysis.
- **Independent extension analysis**: designing a brand-heterogeneity extension that tests whether the NJ–PA employment-change differences vary across Burger King, KFC, Roy Rogers, and Wendy's; using brand dummies and interaction terms in OLS with HC1 heteroskedasticity-robust standard errors, a joint Wald F test, and 95% confidence-interval plots; and a robustness check that excludes permanently closed restaurants.
- **Report and documentation**: helping to organize and draft parts of the research report, and files such as README.md and skills/SKILL.md, to improve the transparency and reproducibility of the workflow.

## 2. How I checked the AI-generated code, analysis, and writing

I did not assume that the AI-generated code and explanations were correct. Instead, I compared the results with the original paper, inspected the intermediate outputs, and asked for revisions whenever I found inconsistencies. The checks, output by output, were as follows:

- **Table 2**: compared the replicated descriptive statistics with Table 2 of the original paper; found and recorded variable-definition differences — the full-time-employee percentage uses an alternative definition, and the Wave-2 "special recruiting program" is not equivalent to the paper's cash recruiting bonus.
- **Table 3**: compared the employment means and changes with Table 3 of the paper; checked how permanent and temporary closures affected the results; found that some standard errors are approximate and do not fully account for the within-store covariance between the two waves, and retained this limitation.
- **Table 4**: compared the sample size, the mean and standard deviation of the outcome, the regression coefficients, the standard errors, and other statistics; and checked the sample-selection diagnostics, the Wave-2 wage missingness, and the treatment of permanently closed restaurants.
- **Independent Extension**: checked each brand's employment-change estimate, robust standard error, confidence interval, and the joint heterogeneity test; distinguished single-coefficient significance from the joint cross-brand heterogeneity test; and considered the multiple-comparison and small-sample limitations.

## 3. Important AI errors or suggestions I corrected or rejected

- **Corrected the Table 4 sample size**: the AI's initial code gave 351 restaurants, and another sample-selection rule gave 365, while the original paper uses 357. By checking the Wave-2 wage missingness and the treatment of permanently closed restaurants, I corrected the selection rule to reach 357. I also recognize that a matching sample size does not fully prove that the sample construction is identical to the paper's.
- **Refused to modify the Model (v) coefficient**: the coefficients of Models (i)–(iv) match the paper to two decimal places, but Model (v) replicates at about 11.98 versus 11.91 in the paper. I did not adjust the result to the paper's value; I kept and recorded the difference.
- **Identified and recorded biased variable definitions**: in Table 2, the AI used alternative definitions for some variables (the full-time share and the Wave-2 recruiting program). I did not treat them as equivalent to the paper's definitions, nor did I adjust the values; I recorded the differences explicitly.
- **Retained rather than concealed the approximation**: some Table 3 standard errors ignore the within-store covariance between the two waves. I recognized this as an approximation and honestly retained the limitation rather than presenting the results as more precise.

## 4. Conclusion

I treated AI-generated suggestions as assistance rather than authoritative answers; I verified every result against the original paper and the available data, and I take responsibility for the final analysis, interpretation, and conclusions. The project provides the Python code, the processed data, the replication tables, the figures, and the related documentation to support a reproducible workflow.
