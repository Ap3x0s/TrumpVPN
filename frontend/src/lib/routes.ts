export const ROUTES = {
  landing: "/",
  login: "/login",
  checkout: (planId: string) => `/checkout/${planId}`,
  pay: (invoiceId: number | string) => `/pay/${invoiceId}`,
  cabinet: "/cabinet",
} as const;
