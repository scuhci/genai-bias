library(visreg)

proportions = read.csv("scripts/output_converted.csv")
m_hispanic.stereotyped = glm(genai_p_hispanic ~ I(bls_p_hispanic - 0.5), 
                          family=quasibinomial, data=proportions, weights=genai_n)


pdf("visreg_hispanic_comparison.pdf", width=8, height=6)
par(
  cex.main = 1.5,   # title
  cex.lab  = 1.5,   # axis labels
  cex.axis = 1.3,   # axis tick labels
  mar      = c(5, 5, 4, 2)  # give a bit more margin for big text
)

visreg(
  m_hispanic.stereotyped,
  "bls_p_hispanic",
  scale = "response",
  rug   = FALSE,
  main  = "Difference in Representation Across 40 Career Terms \nRace: hispanic",
  xlab  = "BLS % hispanic",
  ylab  = "GPT-4 % hispanic"
)

points(genai_p_hispanic ~ bls_p_hispanic, data=proportions, pch=20)
#add some reference lines
abline(coef=c(0,1), lty="dashed")
abline(v=.5, lty="dashed")

dev.off()


