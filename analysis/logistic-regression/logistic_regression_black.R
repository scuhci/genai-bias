install.packages("visreg")
library(visreg)

proportions = read.csv("../../scripts/output_converted.csv")
m_black.stereotyped = glm(search_p_black ~ I(bls_p_black - 0.5), 
                          family=quasibinomial, data=proportions, weights=search_n)

visreg(m_black.stereotyped, "bls_p_black", scale="response", rug=FALSE)
points(search_p_black ~ bls_p_black, data=proportions, pch=20)
#add some reference lines
abline(coef=c(0,1), lty="dashed")
abline(v=.5, lty="dashed")


