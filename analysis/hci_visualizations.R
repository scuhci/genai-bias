# Load libraries
library(ggplot2)
library(dplyr)
library(readr)
library(plotly)
library(tidyr)

# Set working directory
setwd("/Users/aadisudan/Desktop")
getwd()

# Load and clean data
df <- read.csv("police_openai.csv")
colnames(df) <- c("Name", "Age", "Gender", "Ethnicity/Race", "Income", "Primary Motivations", "Short Biography")

# Clean race
df_race <- df %>%
  mutate(`Ethnicity/Race` = case_when(
    `Ethnicity/Race` %in% c("White", "Caucasian", "White/Caucasian") ~ "White",
    `Ethnicity/Race` %in% c("Black", "African American", "Black or African American", "Black/African American") ~ "Black",
    `Ethnicity/Race` %in% c("Asian") ~ "Asian",
    `Ethnicity/Race` %in% c("Hispanic", "Hispanic (Mexican American)", "Hispanic or Latino", "Hispanic/Latina", "Hispanic/Latino", "Hispanic/Latinx") ~ "Hispanic",
    TRUE ~ NA_character_
  )) %>%
  filter(!is.na(`Ethnicity/Race`)) %>%
  group_by(`Ethnicity/Race`) %>%
  summarise(Count = n())

# Summarize women
df_women <- df %>%
  filter(Gender == "Female") %>%
  summarise(Count = n()) %>%
  mutate(`Ethnicity/Race` = "Women")

# Combine race and women
df_combined <- bind_rows(df_race, df_women)

# Calculate GenAI percentages
total_genai <- sum(df_combined$Count)
df_combined <- df_combined %>%
  mutate(
    GenAI_percent = (Count / total_genai) * 100,
    BLS_percent = c(2.8, 14.2, 16.7, 81.4, 14.4)  # BLS percentages: White, Black, Asian, Hispanic, Women
  )

# Reshape to long format
df_long <- pivot_longer(
  df_combined,
  cols = c("GenAI_percent", "BLS_percent"),
  names_to = "Source",
  values_to = "Percent"
)

# Plot 1 
ggplot(df_long, aes(x = `Ethnicity/Race`, y = Percent, color = Source, shape = Source)) +
  geom_point(size = 4) +
  labs(
    title = "Police Officer Demographics in GPT 4.0 vs BLS",
    x = "Category",
    y = "%"
  ) +
  theme_minimal() +
  scale_color_manual(values = c("BLS_percent" = "lightcoral", "GenAI_percent" = "skyblue")) +
  theme(text = element_text(size = 14))

# Calculate percent difference (GenAI - BLS)
df_combined <- df_combined %>%
  mutate(Difference = GenAI_percent - BLS_percent)

# Plot bar chart of differences
ggplot(df_combined, aes(x = `Ethnicity/Race`, y = Difference, fill = Difference > 0)) +
  geom_bar(stat = "identity", width = 0.6, color = "black") +
  geom_text(aes(label = paste0(round(Difference, 1), "%")), vjust = ifelse(df_combined$Difference > 0, -0.5, 1.5), size = 5) +
  scale_fill_manual(values = c("TRUE" = "skyblue", "FALSE" = "lightcoral")) +
  labs(
    title = "Difference in Police Officer Demographics: GPT 4.0 vs BLS",
    x = "Category",
    y = "Difference (%)",
    fill = "Overrepresented"
  ) +
  geom_hline(yintercept = 0, linetype = "dashed") +
  theme_minimal() +
  theme(text = element_text(size = 14))
