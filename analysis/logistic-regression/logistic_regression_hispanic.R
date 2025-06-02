install.packages("visreg")
library(visreg)

proportions = read.csv("../../scripts/output_converted.csv")
m_hispanic.stereotyped = glm(search_p_hispanic ~ I(bls_p_hispanic - 0.5), 
                          family=quasibinomial, data=proportions, weights=search_n)

visreg(m_hispanic.stereotyped, "bls_p_hispanic", scale="response", rug=FALSE)
points(search_p_hispanic ~ bls_p_hispanic, data=proportions, pch=20)
#add some reference lines
abline(coef=c(0,1), lty="dashed")
abline(v=.5, lty="dashed")


