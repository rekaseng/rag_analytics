import streamlit as st


def ragas_ticket_selector(filtered_df):
    if filtered_df.empty:
        st.info("No tickets match current filters.")
        return None

    selectable_df = filtered_df[["ticket_id"]].drop_duplicates().copy()
    selectable_df.insert(0, "select", False)

    edited_df = st.data_editor(
        selectable_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "select": st.column_config.CheckboxColumn(
                "Select",
                help="Select ONE ticket"
            )
        },
        disabled=["ticket_id"],
        height=250
    )

    selected_rows = edited_df[edited_df["select"]]

    if len(selected_rows) == 1:
        return selected_rows.iloc[0]["ticket_id"]

    if len(selected_rows) > 1:
        st.warning("Please select **only one** ticket.")

    return None


def render_context_table(context_df, ticket_id):
    st.subheader(f"📄 Contexts for Ticket: {ticket_id}")

    related_contexts = context_df[
        context_df["ticket_id"] == ticket_id
    ]

    if related_contexts.empty:
        st.info("No contexts found for this ticket.")
        return

    st.dataframe(
        related_contexts,
        use_container_width=True,
        height=420
    )
