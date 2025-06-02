install.packages("visreg")
library(visreg)

proportions = read.csv("../../scripts/output_converted.csv")
m_white.stereotyped = glm(search_p_white ~ I(bls_p_white - 0.5), 
                          family=quasibinomial, data=proportions, weights=search_n)

visreg(m_white.stereotyped, "bls_p_white", scale="response", rug=FALSE)
points(search_p_white ~ bls_p_white, data=proportions, pch=20)
#add some reference lines
abline(coef=c(0,1), lty="dashed")
abline(v=.5, lty="dashed")


