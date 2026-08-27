"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { api, ApiError, type Transaction } from "@/lib/api";
import { Alert, Badge, Button, Card, CardBody, Spinner } from "@/components/ui";
import { formatCurrency, formatDateTime } from "@/lib/format";

export default function HistoryPage() {
  const { token, wallet } = useAuth();
  const [rows, setRows] = useState<Transaction[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (nextCursor: string | null) => {
      if (!token || !wallet) return;
      try {
        const res = await api.history(token, wallet.id, nextCursor, 15);
        setRows((prev) => (nextCursor ? [...prev, ...res.data] : res.data));
        setCursor(res.next_cursor);
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Could not load history.",
        );
      }
    },
    [token, wallet],
  );

  useEffect(() => {
    if (!token || !wallet) return;
    setInitialLoading(true);
    load(null).finally(() => setInitialLoading(false));
  }, [token, wallet, load]);

  async function loadMore() {
    setLoadingMore(true);
    await load(cursor);
    setLoadingMore(false);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">
          Transaction history
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Cursor-paginated ledger, newest first.
        </p>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <Card>
        <CardBody className="p-0 sm:p-0">
          {initialLoading ? (
            <div className="flex justify-center py-16">
              <Spinner className="h-7 w-7 text-brand-600" />
            </div>
          ) : rows.length === 0 ? (
            <p className="py-16 text-center text-sm text-slate-500">
              No transactions found.
            </p>
          ) : (
            <>
              <div className="hidden grid-cols-[1fr_auto_auto] gap-4 border-b border-slate-100 px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-400 sm:grid">
                <span>Counterparty</span>
                <span className="text-right">Amount</span>
                <span className="text-right">Status</span>
              </div>
              <ul className="divide-y divide-slate-100">
                {rows.map((tx) => (
                  <li
                    key={tx.id}
                    className="grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-1 px-6 py-4 sm:grid-cols-[1fr_auto_auto]"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-800">
                        {tx.counterparty_name ?? "—"}
                      </p>
                      <p className="text-xs text-slate-500">
                        <span
                          className={
                            "font-semibold " +
                            (tx.type === "CREDIT"
                              ? "text-emerald-600"
                              : "text-slate-600")
                          }
                        >
                          {tx.type}
                        </span>
                        {" · "}
                        {formatDateTime(tx.created_at)}
                      </p>
                    </div>
                    <p
                      className={
                        "text-right text-sm font-semibold " +
                        (tx.type === "CREDIT"
                          ? "text-emerald-600"
                          : "text-slate-800")
                      }
                    >
                      {tx.type === "CREDIT" ? "+" : "−"}
                      {formatCurrency(tx.amount, wallet?.currency)}
                    </p>
                    <div className="col-start-2 row-start-2 flex justify-end sm:col-start-3 sm:row-start-1">
                      <Badge
                        tone={
                          tx.status === "SUCCESS"
                            ? "green"
                            : tx.status === "FAILED"
                              ? "red"
                              : "slate"
                        }
                      >
                        {tx.status}
                      </Badge>
                    </div>
                  </li>
                ))}
              </ul>
              {cursor && (
                <div className="border-t border-slate-100 p-4">
                  <Button
                    variant="secondary"
                    onClick={loadMore}
                    loading={loadingMore}
                    className="w-full"
                  >
                    Load more
                  </Button>
                </div>
              )}
            </>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
