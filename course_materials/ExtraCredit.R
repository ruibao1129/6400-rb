2 + 3
5 * 4

10 / 2
(3 + 5) ^2

x <- 5
y <- 10
z <- x + y
z
# This is a comment
x <- 10 # Assign 10 to x

prices <- c (100 , 150 , 200 , 175)
mean ( prices )
sd ( prices )
length ( prices )

square <- function ( x ) {
  return ( x ^2)
}
square (6)

for ( i in 1:5) {
  print ( i )
}

# Sample data
x <- c(10, 12, 8, 11, 9)

# Step 1: Compute the mean
mean_x <- mean(x)

# Step 2: Initialize a variable for the sum of squared differences
sum_sq_diff <- 0

# Step 3: Loop through each value
for (value in x) {
  sum_sq_diff <- sum_sq_diff + (value - mean_x)^2
}

# Step 4: Divide by n - 1 to calculate the sample variance
variance <- sum_sq_diff / (length(x) - 1)

# Display the results
print(mean_x)
print(sum_sq_diff)
print(variance)

# Check the answer using R's built-in variance function
print(var(x))




# Install ( only once )
install.packages ( " ggplot2 " )
# Load ( each session )
library ( ggplot2 )

x <- c (1 , 2 , 3 , 4 , 5)
y <- c (2 , 4 , 6 , 8 , 10)
data <- data.frame (x , y )
ggplot ( data , aes ( x = x , y = y ) ) +
  geom_point () +
  labs ( title = " Simple Scatterplot " )


# Load ggplot2
library(ggplot2)

# Create sample data
x <- c(1, 1, 2, 3, 3, 3, 3, 4, 4, 5)

my_data <- data.frame(x)

# Create a histogram
ggplot(my_data, aes(x = x)) +
  geom_histogram(
    binwidth = 1,
    fill = "skyblue",
    color = "black"
  ) +
  labs(
    title = "Histogram of X Values",
    x = "X Value",
    y = "Frequency"
  )

student_data <- read.csv(file.choose())

# View the first few rows
head ( data )
# View the structure of the data
str ( data )
# See summary statistics for each column
summary ( data )
# View the column names
colnames ( data )

age <- data $ age
age
mean ( age )

? mean # Help on mean ()
help ( sd ) # Help on sd ()


install.packages("tidyquant")
install.packages("tidyverse")
install.packages("ggplot2")
install.packages("dplyr")
install.packages("GGally")
install.packages("quadprog")


# load libraries

library(tidyquant)
library(tidyverse)
library(ggplot2)
library(dplyr)
library(GGally)
library(quadprog)

# get historical data for a single stock. E.g., "TSLA" Tesla or "GOOG" Google

tsla <- tq_get(
  "TSLA",
  get = "stock.prices",
  from = "2010-01-01"
) %>%
  tq_transmute(
    mutate_fun = to.period,
    period = "months"
  )

ggplot(tsla, aes(date, close)) +
  geom_line()

# Get monthly returns for TSLA from 2010

tsla_returns <- tq_get(
  "TSLA",
  get = "stock.prices",
  from = "2010-01-01"
) %>%
  tq_transmute(
    select = adjusted,
    mutate_fun = periodReturn,
    period = "monthly",
    col_rename = "monthly_return"
  )

ggplot(tsla_returns, aes(x = date, y = monthly_return)) +
  geom_line() +
  labs(
    title = "TSLA Monthly Returns",
    x = "Date",
    y = "Return"
  )


# Define tickers

tickers <- c("GOOG", "JNJ", "WMT")


# Get monthly returns for all stocks

returns_data <- tq_get(
  tickers,
  get = "stock.prices",
  from = "2005-01-01"  # GOOG IPO was in 2004
) %>%
  group_by(symbol) %>%
  tq_transmute(
    select = adjusted,
    mutate_fun = periodReturn,
    period = "monthly",
    col_rename = "monthly_return"
  ) %>%
  ungroup() %>%
  tidyr::pivot_wider(
    names_from = symbol,
    values_from = monthly_return
  )


# Remove rows with missing data

returns_data_clean <- na.omit(returns_data)


# View a correlation scatterplot matrix

ggpairs(
  returns_data_clean[, -1],
  title = "Monthly Return Correlation Matrix: GOOG, JNJ, WMT"
)

# Step 1: Get GOOG monthly returns

goog <- tq_get(
  "GOOG",
  get = "stock.prices",
  from = "2010-01-01"
) %>%
  tq_transmute(
    select = adjusted,
    mutate_fun = periodReturn,
    period = "monthly",
    col_rename = "goog_return"
  )


# Step 2: Get S&P 500 returns (market proxy)

sp500 <- tq_get(
  "^GSPC",
  get = "stock.prices",
  from = "2010-01-01"
) %>%
  tq_transmute(
    select = adjusted,
    mutate_fun = periodReturn,
    period = "monthly",
    col_rename = "market_return"
  )


# Step 3: Join returns

returns <- left_join(goog, sp500, by = "date")


# Step 4: Set risk-free rate (monthly)

rf_annual <- 0.0432
rf_monthly <- rf_annual / 12  # = 0.0036


# Step 5: Calculate excess returns

returns <- returns %>%
  mutate(
    excess_goog = goog_return - rf_monthly,
    excess_market = market_return - rf_monthly
  )


# Step 6: Sharpe Ratio

sharpe_ratio <- mean(
  returns$excess_goog,
  na.rm = TRUE
) / sd(
  returns$goog_return,
  na.rm = TRUE
)

print(paste("Sharpe Ratio:", round(sharpe_ratio, 3)))


# Step 7: Jensen's Alpha via CAPM regression

model <- lm(excess_goog ~ excess_market, data = returns)

alpha <- coef(model)[1]
beta <- coef(model)[2]


# Monthly Jensen's Alpha

print(paste("Beta:", round(beta, 3)))

print(
  paste(
    "Jensen's Alpha (monthly):",
    round(alpha, 5)
  )
)


# Annualized Jensen's Alpha

jensen_alpha_annualized <- (1 + alpha)^12 - 1

print(
  paste(
    "Jensen's Alpha (annualized):",
    round(jensen_alpha_annualized, 4)
  )
)

# Step 1: Get GOOG monthly returns

goog <- tq_get(
  "GOOG",
  get = "stock.prices",
  from = "2010-01-01"
) %>%
  tq_transmute(
    select = adjusted,
    mutate_fun = periodReturn,
    period = "monthly",
    col_rename = "goog_return"
  )


# Step 2: Get S&P 500 returns (market proxy)

sp500 <- tq_get(
  "^GSPC",
  get = "stock.prices",
  from = "2010-01-01"
) %>%
  tq_transmute(
    select = adjusted,
    mutate_fun = periodReturn,
    period = "monthly",
    col_rename = "market_return"
  )


# Step 3: Join returns

returns <- left_join(goog, sp500, by = "date")


# Step 4: Set risk-free rate (monthly)

rf_annual <- 0.0432
rf_monthly <- rf_annual / 12  # = 0.0036


# Step 5: Calculate excess returns

returns <- returns %>%
  mutate(
    excess_goog = goog_return - rf_monthly,
    excess_market = market_return - rf_monthly
  )


# Step 6: Sharpe Ratio

sharpe_ratio <- mean(
  returns$excess_goog,
  na.rm = TRUE
) / sd(
  returns$goog_return,
  na.rm = TRUE
)

print(paste("Sharpe Ratio:", round(sharpe_ratio, 3)))


# Step 7: Jensen's Alpha via CAPM regression

model <- lm(excess_goog ~ excess_market, data = returns)

alpha <- coef(model)[1]
beta <- coef(model)[2]


# Monthly Jensen's Alpha

print(paste("Beta:", round(beta, 3)))

print(
  paste(
    "Jensen's Alpha (monthly):",
    round(alpha, 5)
  )
)


# Annualized Jensen's Alpha

jensen_alpha_annualized <- (1 + alpha)^12 - 1

print(
  paste(
    "Jensen's Alpha (annualized):",
    round(jensen_alpha_annualized, 4)
  )
)


12:57















portfolio_returns <- returns_data_clean %>%
  select(-date)

R <- as.matrix(portfolio_returns)


# Mean returns & covariance (monthly)

mu <- colMeans(R)
Sigma <- cov(R)


# Risk-free rate (monthly)

rf <- rf_monthly


# Sharpe ratio function (negative for minimization)

neg_sharpe <- function(w, mu, Sigma, rf) {
  w <- w / sum(w)  # enforce sum of weights = 1
  port_ret <- sum(w * mu)
  port_sd <- sqrt(t(w) %*% Sigma %*% w)
  -(port_ret - rf) / port_sd
}


# Initial guess (equal weights)

n_assets <- ncol(R)
w0 <- rep(1 / n_assets, n_assets)


# Optimize (no short-selling)

opt <- optim(
  par = w0,
  fn = neg_sharpe,
  mu = mu,
  Sigma = Sigma,
  rf = rf,
  method = "L-BFGS-B",
  lower = rep(0, n_assets),
  upper = rep(1, n_assets)
)


# Optimal weights

weights <- opt$par / sum(opt$par)
names(weights) <- colnames(R)

print("Optimal Portfolio Weights (Max Sharpe Ratio):")
round(weights, 4)


# Portfolio performance

portfolio_return <- sum(weights * mu)

portfolio_sd <- sqrt(
  t(weights) %*% Sigma %*% weights
)

portfolio_sharpe <- (
  portfolio_return - rf
) / portfolio_sd


cat(
  "\nPortfolio Expected Monthly Return:",
  round(portfolio_return, 4)
)

cat(
  "\nPortfolio Monthly Volatility:",
  round(portfolio_sd, 4)
)

cat(
  "\nPortfolio Sharpe Ratio:",
  round(portfolio_sharpe, 4)
)







