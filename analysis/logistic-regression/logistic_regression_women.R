install.packages("visreg")
library(visreg)

proportions = read.csv("../../scripts/output_converted.csv")
m_women.stereotyped = glm(search_p_women ~ I(bls_p_women - 0.5), 
                    family=quasibinomial, data=proportions, weights=search_n)

visreg(m_women.stereotyped, "bls_p_women", scale="response", rug=FALSE)
points(search_p_women ~ bls_p_women, data=proportions, pch=20)
#add some reference lines
abline(coef=c(0,1), lty="dashed")
abline(v=.5, lty="dashed")


