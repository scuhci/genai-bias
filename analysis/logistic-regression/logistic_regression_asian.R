library(visreg)

proportions = read.csv("scripts/output_converted.csv")
m_asian.stereotyped = glm(genai_p_asian ~ I(bls_p_asian - 0.5), 
                          family=quasibinomial, data=proportions, weights=genai_n)


pdf("visreg_asian_comparison.pdf", width=8, height=6)
par(
  cex.main = 1.5,   # title
  cex.lab  = 1.5,   # axis labels
  cex.axis = 1.3,   # axis tick labels
  mar      = c(5, 5, 4, 2)  # give a bit more margin for big text
)

visreg(
  m_asian.stereotyped,
  "bls_p_asian",
  scale = "response",
  rug   = FALSE,
  main  = "Difference in Representation Across 40 Career Terms \nRace: asian",
  xlab  = "BLS % asian",
  ylab  = "GPT-4 % asian"
)

points(genai_p_asian ~ bls_p_asian, data=proportions, pch=20)
#add some reference lines
abline(coef=c(0,1), lty="dashed")
abline(v=.5, lty="dashed")

dev.off()

