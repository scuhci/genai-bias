install.packages("visreg")
library(visreg)

proportions = read.csv("../../scripts/output_converted.csv")
m_asian.stereotyped = glm(search_p_asian ~ I(bls_p_asian - 0.5), 
                          family=quasibinomial, data=proportions, weights=search_n)

visreg(m_asian.stereotyped, "bls_p_asian", scale="response", rug=FALSE)
points(search_p_asian ~ bls_p_asian, data=proportions, pch=20)
#add some reference lines
abline(coef=c(0,1), lty="dashed")
abline(v=.5, lty="dashed")


